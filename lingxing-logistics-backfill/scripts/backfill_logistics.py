"""海运费用明细 -> 领星 ERP 物流信息回填

四个子命令，按顺序使用：
  parse   读取员工上传的 xlsx，解析成按备货单分组的 groups.json（不联网）
  plan    对比 groups.json 与 ERP 现值 erp.json，生成 plan.json + plan.md（不联网、不写入）
  write   按 plan.json 调用写入接口，逐单输入 yes 确认（联网，会写入 ERP）
  verify  用写入后的 ERP 现值 erp_after.json 核对是否落到正确位置（不联网）

ERP 现值 erp.json / erp_after.json 由 Claude 通过 MCP 读取后生成，格式见 SKILL.md"读取结果格式"。
"""
import argparse, base64, copy, hashlib, json, os, re, sys, time, urllib.parse, urllib.request
from datetime import datetime

import openpyxl

sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "https://openapi.lingxing.com"
AUTH_URL = f"{BASE_URL}/api/auth-server/oauth/access-token"
APP_ID = os.environ.get("LINGXING_APP_ID", "")
APP_SECRET = os.environ.get("LINGXING_APP_SECRET", "")
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))
RATE_SLEEP = {"FBA": 2.0, "OWS": 1.2, "FBT": 1.2}
WRITE_ENDPOINT = {
    "FBA": "/erp/sc/routing/storage/shipment/updateListLogistics",
    "OWS": "/erp/sc/routing/owms/inbound/updateLogistics",
    "FBT": "/basicOpen/multiplatform/shippingList/updateLogistics",
}
STA_LIST_BOXES = "/amzStaServer/openapi/inbound-shipment/listShipmentBoxes"
STA_UPDATE_TRACK = "/amzStaServer/openapi/inbound-shipment/updateShipmentTrack"

PROVIDER_IDS = {"捷立信": "10125", "万达": "10697", "积米": "15889", "合信": "16001", "联宇": "13130"}
PROVIDER_NAMES = {v: k for k, v in PROVIDER_IDS.items()}
CHANNEL_IDS = {
    ("10125", "海卡"): "14316", ("10125", "空运"): "14993",
    ("10697", "海运"): "35158", ("10697", "空运"): "15805",
    ("15889", "海运"): "30589", ("16001", "海运"): "27570",
    ("13130", "快递"): "22109",
}
CHANNEL_NAMES = {v: k for k, v in CHANNEL_IDS.items()}
# 表格 H 列出现过的渠道名。不在此表中的名称一律标记为"需人工"，不自动映射。
KNOWN_H = {
    "以星海派", "以星卡派", "以星海卡", "以星", "美森", "美森特快", "美国干货海卡", "美国干货海派",
    "ZIM快船海派", "大陆UPS红单包税特快", "空运", "海运", "快递", "海卡", "海派",
    "Z快线-美西-快递派", "穿越-美西-拆派", "Z快线-美西-先查后装",
}
NON_TRACKING = {"卡派"}
UNSET = ("", None, "0", "0.0", "0.00")


def classify(sn):
    if re.fullmatch(r"OWS\d+", sn):
        return "OWS"
    if re.fullmatch(r"SP2026\d{11}", sn):
        return "FBT"
    if re.fullmatch(r"SP26\d{7}", sn):
        return "FBA"
    return None


def provider_id_of(name):
    """ERP 物流商全称（如 '广州合信物流'）→ 物流商ID。"""
    for key, pid in PROVIDER_IDS.items():
        if key and key in (name or ""):
            return pid
    return ""


def map_channel(provider_id, h):
    """返回 (渠道ID, 渠道名, 备注)。无法判断时渠道ID为 None。"""
    if not h:
        return None, None, "表格渠道为空"
    if h not in KNOWN_H:
        return None, None, f"渠道名 '{h}' 不在已知映射表中"
    if provider_id == "10125":
        if "海运" in h:
            return None, None, "捷立信没有海运渠道"
        name = "空运" if "空" in h else "海卡"
    elif provider_id == "10697":
        if "空" in h:
            name = "空运"
        elif "海" in h:
            name = "海运"
        else:
            return None, None, "万达渠道无法判断"
    elif provider_id in ("15889", "16001"):
        if "海" not in h or "空" in h:
            return None, None, f"{PROVIDER_NAMES[provider_id]}只有海运渠道，表格为'{h}'"
        name = "海运"
    elif provider_id == "13130":
        name = "快递"
    else:
        return None, None, "物流商未知"
    return CHANNEL_IDS[(provider_id, name)], name, ""


# ---------------------------------------------------------------- parse

def parse_xlsx(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.active
    merge_map = {}
    for mr in ws.merged_cells.ranges:
        if mr.min_col == 3 and mr.max_col == 3:
            sn_val = str(ws.cell(mr.min_row, 3).value or "").strip()
            if sn_val:
                for r in range(mr.min_row, mr.max_row + 1):
                    merge_map[r] = sn_val

    groups, carry_sn, issues = {}, "", []
    for r in range(2, ws.max_row + 1):
        a_val = ws.cell(r, 1).value
        try:
            float(a_val)
        except (TypeError, ValueError):
            continue
        if r in merge_map:
            sn = merge_map[r]
            carry_sn = ""
        else:
            cv = ws.cell(r, 3).value
            explicit = str(cv).strip() if cv else ""
            if explicit and classify(explicit):
                sn, carry_sn = explicit, explicit
            elif carry_sn:
                sn = carry_sn
            else:
                continue
        sn_type = classify(sn)
        if not sn_type:
            continue
        g = groups.setdefault(sn, {"type": sn_type, "rows": []})
        q_raw = ws.cell(r, 17).value
        try:
            q = round(float(q_raw), 2) if q_raw not in (None, "") else 0.0
        except (TypeError, ValueError):
            q = 0.0
            issues.append(f"行{r} Q列不是数字: {q_raw!r}")
        g["rows"].append({
            "row": r,
            "F": str(ws.cell(r, 6).value or "").strip(),
            "G": str(ws.cell(r, 7).value or "").strip(),
            "H": re.sub(r"\s+", "", str(ws.cell(r, 8).value or "")),
            "I": re.sub(r"\s+", "", str(ws.cell(r, 9).value or "")),
            "Q": q,
        })
    for sn, g in groups.items():
        f_parts = [x["F"] for x in g["rows"] if x["F"]]
        if any("、" in x or "，" in x or " " in x for x in f_parts):
            issues.append(f"{sn}: F列含顿号/逗号/空格，需人工确认")
        if len(set(f_parts)) != len(f_parts):
            issues.append(f"{sn}: F列有重复值，需人工确认")
        for x in g["rows"]:
            if x["G"] in NON_TRACKING:
                x["G_skip"] = True
    return {"groups": groups, "issues": issues, "source": path}


# ---------------------------------------------------------------- plan

def _norm_list(v):
    if v is None:
        return []
    if isinstance(v, str):
        return [v] if v else []
    return [str(x) for x in v if x]


def plan_one(sn, g, erp):
    """erp 字段（由 Claude 从 MCP 读取后填入，见 SKILL）:
    provider_name, channel_name, tracking_number(物流商单号), tracking_list(快递号列表), fee(金额字符串),
    logisticsInfo(仅 FBT: 列表，元素含 logisticsNumber/trackingNumber/transportationCost)
    """
    out = {"sn": sn, "type": g["type"], "fields": {}, "notes": []}
    rows = g["rows"]
    f_vals = [x["F"] for x in rows if x["F"]]
    f_target = ".".join(f_vals) if f_vals else ""
    i_name = next((x["I"] for x in rows if x["I"]), "")
    h_name = next((x["H"] for x in rows if x["H"]), "")
    q_sum = round(sum(x["Q"] for x in rows), 2)
    g_list = [x["G"] for x in rows if x["G"] and x["G"] not in NON_TRACKING]

    erp_f = (erp.get("tracking_number") or "").strip()
    erp_provider = erp.get("provider_name") or ""
    erp_channel = erp.get("channel_name") or ""
    erp_pid = provider_id_of(erp_provider)
    erp_cid = CHANNEL_IDS.get((erp_pid, erp_channel), "")
    erp_tracks = _norm_list(erp.get("tracking_list"))
    erp_fee = erp.get("fee")

    # F 物流商单号（A 类）
    f_bad = bool(f_vals) and (any(re.search(r"[、，\s]", x) for x in f_vals) or len(set(f_vals)) != len(f_vals)
                              or len(set(".".join(f_vals).split("."))) != len(".".join(f_vals).split(".")))
    if not f_target:
        out["fields"]["F"] = {"action": "跳过", "erp": erp_f, "target": "", "why": "表格为空"}
    elif f_bad:
        out["fields"]["F"] = {"action": "需人工", "erp": erp_f, "target": f_target, "why": "表格 F 列格式可疑或重复"}
    elif f_target == erp_f:
        out["fields"]["F"] = {"action": "无变化", "erp": erp_f, "target": f_target}
    else:
        out["fields"]["F"] = {"action": "写入" if not erp_f else "覆盖", "erp": erp_f, "target": f_target}

    # I 物流商（A 类）
    tgt_pid = PROVIDER_IDS.get(i_name, "")
    if not i_name:
        out["fields"]["I"] = {"action": "跳过", "erp": erp_provider, "target": "", "why": "表格为空"}
    elif not tgt_pid:
        out["fields"]["I"] = {"action": "需人工", "erp": erp_provider, "target": i_name, "why": f"物流商 '{i_name}' 无ID映射"}
    elif tgt_pid == erp_pid:
        out["fields"]["I"] = {"action": "无变化", "erp": erp_provider, "target": i_name}
    else:
        out["fields"]["I"] = {"action": "写入" if not erp_provider else "覆盖", "erp": erp_provider, "target": i_name, "target_id": tgt_pid}

    # H 渠道（A 类）；FBT 渠道跟随物流商自动关联，不写
    tgt_pid_for_h = tgt_pid or erp_pid
    cid, cname, why = map_channel(tgt_pid_for_h, h_name)
    if g["type"] == "FBT":
        out["fields"]["H"] = {"action": "跳过", "erp": erp_channel, "target": h_name,
                              "why": "FBT 渠道跟随物流商自动关联，不单独写入"}
    elif not h_name:
        out["fields"]["H"] = {"action": "跳过", "erp": erp_channel, "target": "", "why": "表格为空"}
    elif cid is None:
        out["fields"]["H"] = {"action": "需人工", "erp": erp_channel, "target": h_name, "why": why}
    elif cid == erp_cid:
        out["fields"]["H"] = {"action": "无变化", "erp": erp_channel, "target": cname, "target_id": cid}
    else:
        out["fields"]["H"] = {"action": "写入" if not erp_channel else "覆盖", "erp": erp_channel, "target": cname, "target_id": cid}

    # G 快递号（B 类，仅 ERP 空才写）
    if g["type"] == "FBT":
        erp_g = [str(i.get("trackingNumber") or "") for i in erp.get("logisticsInfo") or [] if i.get("trackingNumber")]
    else:
        erp_g = erp_tracks
    if not g_list:
        out["fields"]["G"] = {"action": "跳过", "erp": erp_g, "target": [], "why": "表格无快递号（或仅卡派）"}
    elif erp_g:
        out["fields"]["G"] = {"action": "跳过", "erp": erp_g, "target": g_list, "why": "ERP 已有快递号，不覆盖"}
    elif g["type"] == "FBA":
        out["fields"]["G"] = {"action": "写入", "erp": [], "target": g_list}
    else:
        out["fields"]["G"] = {"action": "写入", "erp": [], "target": g_list}

    # Q 金额（B 类，ERP 空或 0 才写）
    erp_fee_s = str(erp_fee) if erp_fee not in (None, "") else ""
    if q_sum <= 0:
        out["fields"]["Q"] = {"action": "跳过", "erp": erp_fee_s, "target": "", "why": "表格金额为 0"}
    elif erp_fee_s in UNSET:
        out["fields"]["Q"] = {"action": "写入", "erp": erp_fee_s, "target": f"{q_sum:.2f}"}
    elif abs(float(erp_fee_s) - q_sum) < 0.005:
        out["fields"]["Q"] = {"action": "无变化", "erp": erp_fee_s, "target": f"{q_sum:.2f}"}
    else:
        out["fields"]["Q"] = {"action": "跳过", "erp": erp_fee_s, "target": f"{q_sum:.2f}",
                              "why": f"ERP 已有金额，差额 {q_sum - float(erp_fee_s):+.2f}，需人工确认"}

    if any(v["action"] == "需人工" for v in out["fields"].values()):
        out["needs_review"] = True
    return out


def cmd_plan(args):
    with open(args.groups, encoding="utf-8") as f:
        parsed = json.load(f)
    with open(args.erp, encoding="utf-8") as f:
        erp_all = json.load(f)
    plans = []
    for sn, g in parsed["groups"].items():
        cat = g["type"]
        erp = erp_all.get(cat, {}).get(sn)
        if erp is None:
            plans.append({"sn": sn, "type": cat, "missing_erp": True, "fields": {}, "notes": ["ERP 现值缺失，未对比"]})
            continue
        plans.append(plan_one(sn, g, erp))
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"plans": plans, "issues": parsed.get("issues", []), "source": parsed.get("source")},
                  f, ensure_ascii=False, indent=2)
    md = render_md(plans, parsed.get("issues", []))
    md_path = os.path.splitext(args.out)[0] + ".md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"已生成 {args.out} 与 {md_path}（{len(plans)} 个备货单）")


def render_md(plans, issues):
    counts = {}
    for p in plans:
        for k, v in p.get("fields", {}).items():
            counts[(k, v["action"])] = counts.get((k, v["action"]), 0) + 1
    lines = ["# 回填清单（预览，未写入 ERP）", "", "## 汇总"]
    for (k, act), n in sorted(counts.items()):
        lines.append(f"- {k} {act}: {n}")
    lines.append(f"- 需人工确认的备货单: {sum(1 for p in plans if p.get('needs_review'))}")
    lines.append("")
    for label, want in (("写入", "写入"), ("覆盖", "覆盖"), ("需人工", "需人工"), ("待开发（脚本未实现）", "待开发")):
        group = [p for p in plans if any(v["action"] == want for v in p.get("fields", {}).values())]
        lines.append(f"## {label}（{len(group)} 个备货单）")
        for p in group:
            items = [f"{k}:{v['action']}({v.get('erp')!s}→{v.get('target')!s}{' '+v['why'] if v.get('why') else ''})"
                     for k, v in p["fields"].items() if v["action"] == want]
            lines.append(f"- {p['type']} {p['sn']}: " + "；".join(items))
        lines.append("")
    diffs = [p for p in plans if "差额" in (p.get("fields", {}).get("Q", {}).get("why") or "")]
    if diffs:
        lines.append(f"## 金额差异（ERP 已有金额，未写入，需确认）（{len(diffs)} 个备货单）")
        for p in diffs:
            q = p["fields"]["Q"]
            lines.append(f"- {p['type']} {p['sn']}: ERP {q.get('erp')} / 表格 {q.get('target')}（{q.get('why')}）")
        lines.append("")
    if issues:
        lines.append("## 表格问题（需员工确认）")
        lines += [f"- {x}" for x in issues]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- write

def _aes_encrypt(key, data):
    from Crypto.Cipher import AES
    pad = 16 - len(data) % 16
    cipher = AES.new(key.encode("utf-8"), AES.MODE_ECB)
    return base64.b64encode(cipher.encrypt((data + chr(pad) * pad).encode("utf-8"))).decode("utf-8")


def compute_sign(app_id, params):
    parts = {}
    for k, v in params.items():
        if isinstance(v, (dict, list)):
            parts[k] = json.dumps(v, separators=(",", ":"), ensure_ascii=False)
        elif v == "" or v is None:
            continue
        else:
            parts[k] = str(v)
    sign_string = "&".join(f"{k}={parts[k]}" for k in sorted(parts))
    return _aes_encrypt(app_id, hashlib.md5(sign_string.encode("utf-8")).hexdigest().upper())


_token, _token_expire = None, 0


def get_token():
    global _token, _token_expire
    if _token and time.time() < _token_expire - 60:
        return _token
    body = urllib.parse.urlencode({"appId": APP_ID, "appSecret": APP_SECRET}).encode("utf-8")
    req = urllib.request.Request(AUTH_URL, data=body, method="POST",
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    with OPENER.open(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if str(data.get("code")) not in ("0", "200"):
        raise RuntimeError(f"获取 token 失败: code={data.get('code')} msg={data.get('msg')}")
    _token = data["data"]["access_token"]
    _token_expire = time.time() + data["data"].get("expires_in", 7200)
    return _token


def api_post(path, body):
    token = get_token()
    sign_params = {"app_key": APP_ID, "access_token": token, "timestamp": str(int(time.time()))}
    sign = compute_sign(APP_ID, {**body, **sign_params})
    query = urllib.parse.urlencode({**sign_params, "sign": sign})
    req = urllib.request.Request(f"{BASE_URL}{path}?{query}",
                                 data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                                 method="POST", headers={"Content-Type": "application/json"})
    with OPENER.open(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def sta_list_boxes(sid, shipment_confirmation_id):
    resp = api_post(STA_LIST_BOXES, {"sid": sid, "shipmentConfirmationId": shipment_confirmation_id})
    if resp.get("code") != 0:
        return None, resp.get("msg") or resp.get("message") or str(resp.get("code"))
    boxes = []
    for sl in (resp.get("data") or {}).get("shipmentList", []):
        for pk in sl.get("shipmentPackingList", []):
            bid = pk.get("boxId", "")
            if bid:
                boxes.append(bid)
    return boxes, None


def sta_build_track_plan(erp, target_tracks):
    """Given ERP data with fba_shipments and target tracking numbers,
    query boxes for each shipment and build (shipment, trackBOList) pairs.
    Returns (pairs, error_msg). Each pair: (sid, shipmentConfirmationId, trackBOList)."""
    shipments = erp.get("fba_shipments") or []
    if not shipments:
        return None, "ERP 数据缺少 fba_shipments（需重新 read）"
    all_boxes = []
    for s in shipments:
        boxes, err = sta_list_boxes(s["sid"], s["shipmentConfirmationId"])
        if err:
            return None, f"listShipmentBoxes {s['shipmentConfirmationId']} 失败: {err}"
        for b in boxes:
            all_boxes.append({"sid": s["sid"], "shipmentConfirmationId": s["shipmentConfirmationId"], "boxId": b})
        time.sleep(0.3)
    if len(all_boxes) != len(target_tracks):
        return None, f"box 数 {len(all_boxes)} != 快递号数 {len(target_tracks)}，需人工确认"
    by_ship = {}
    for i, ab in enumerate(all_boxes):
        key = (ab["sid"], ab["shipmentConfirmationId"])
        by_ship.setdefault(key, []).append({"boxId": ab["boxId"], "trackingId": target_tracks[i]})
    pairs = [(sid, cid, tbl) for (sid, cid), tbl in by_ship.items()]
    return pairs, None


def build_body(plan, erp):
    """只把要写的字段放进请求体；全量覆盖接口里未变化的字段用 ERP 现值回传，防止清零。"""
    f, i, h, g, q = (plan["fields"].get(k, {}) for k in "FIHGQ")
    provider_id = i.get("target_id") or provider_id_of(erp.get("provider_name", ""))
    channel_id = h.get("target_id") or CHANNEL_IDS.get((provider_id, erp.get("channel_name", "")), "")
    tracking_no = f["target"] if f.get("action") in ("写入", "覆盖") else (erp.get("tracking_number") or "")
    fee = q["target"] if q.get("action") == "写入" else (str(erp.get("fee") or "") or None)
    new_tracks = g["target"] if g.get("action") == "写入" else []
    erp_tracks = _norm_list(erp.get("tracking_list"))
    tracks = erp_tracks if erp_tracks else new_tracks

    if plan["type"] == "OWS":
        head = {"logistics_tracking_number": tracking_no,
                "tracking_list": [{"tracking_no": t, "transport_type": 1, "order_type_code": 5} for t in tracks]}
        if fee:
            head["actual_expenses_list"] = {"logistics_fee": fee, "logistics_fee_currency": "CNY"}
        body = {"overseas_order_no": plan["sn"], "logistics_list_type": 1, "head_logistics_list": head}
        if provider_id:
            body["logistics_provider_id"] = int(provider_id)
        if channel_id:
            body["logistics_channel_id"] = int(channel_id)
        return body
    if plan["type"] == "FBA":
        head = {"logistics_tracking_number": tracking_no}
        if fee:
            head["actual_expenses_list"] = {"logistics_fee": fee, "logistics_fee_currency": "CNY"}
        item = {"order_sn": plan["sn"], "logistics_list_type": 1, "head_logistics_list": head}
        if provider_id:
            item["logistics_provider_id"] = int(provider_id)
        if channel_id:
            item["logistics_channel_id"] = int(channel_id)
        return {"data": [item]}
    # FBT：logisticsInfo 为覆盖式。逐行合并：F 列以表格为准（A 类）；
    # G、Q 列 ERP 已有值则保留，ERP 为空才写表格值（B 类）；FBT 不写渠道（跟随物流商）
    erp_info = copy.deepcopy(erp.get("logisticsInfo") or [])
    rows = plan.get("rows", [])
    n = max(len(erp_info), len(rows))
    info = []
    for i in range(n):
        e = erp_info[i] if i < len(erp_info) else {}
        r = rows[i] if i < len(rows) else None
        item = dict(e)
        if r is not None and r["F"]:
            item["logisticsNumber"] = r["F"]
        if r is not None and not e.get("trackingNumber") and r["G"] and r["G"] not in NON_TRACKING:
            item["trackingNumber"] = r["G"]
        if r is not None and float(e.get("transportationCost") or 0) == 0 and r["Q"] > 0:
            item["transportationCost"] = f"{r['Q']:.2f}"
            item["transportationCurrency"] = "CNY"
        if item:
            info.append(item)
    item = {"shippingListCode": plan["sn"], "logisticsInfo": info}
    if provider_id:
        item["logisticsProviderId"] = int(provider_id)
    return {"data": [item]}


def cmd_write(args):
    if not APP_ID or not APP_SECRET:
        sys.exit("缺少环境变量 LINGXING_APP_ID / LINGXING_APP_SECRET")
    with open(args.plan, encoding="utf-8") as f:
        plans = json.load(f)["plans"]
    with open(args.erp, encoding="utf-8") as f:
        erp_all = json.load(f)
    with open(args.groups, encoding="utf-8") as f:
        groups = json.load(f)["groups"]
    wanted = set(args.sn) if args.sn else None
    log = []
    for p in plans:
        if wanted and p["sn"] not in wanted:
            continue
        if p.get("needs_review") or p.get("missing_erp"):
            log.append({"sn": p["sn"], "result": "跳过-需人工/缺现值"})
            continue
        if not any(v["action"] in ("写入", "覆盖") for v in p["fields"].values()):
            continue
        erp = erp_all[p["type"]][p["sn"]]
        p = dict(p, rows=groups[p["sn"]]["rows"])

        has_main = any(p["fields"].get(k, {}).get("action") in ("写入", "覆盖") for k in "FIHQ")
        has_fba_track = p["type"] == "FBA" and p["fields"].get("G", {}).get("action") == "写入"

        if has_main:
            body = build_body(p, erp)
            path = WRITE_ENDPOINT[p["type"]]
            print(f"\n== {p['type']} {p['sn']} ==  {path}")
            print(json.dumps(body, ensure_ascii=False, indent=2))
            if args.execute:
                if input("写入以上内容？输入 yes 确认: ").strip() != "yes":
                    log.append({"sn": p["sn"], "result": "用户未确认"})
                    continue
                resp = api_post(path, body)
                ok = str(resp.get("code")) in ("0", "200")
                log.append({"sn": p["sn"], "type": p["type"], "step": "main", "body": body, "resp": resp, "ok": ok, "at": datetime.now().isoformat()})
                print(f"返回: code={resp.get('code')} msg={resp.get('msg')}")
                if not ok:
                    print("接口返回错误，停止后续写入。")
                    break
                time.sleep(RATE_SLEEP[p["type"]])

        if has_fba_track:
            target_tracks = p["fields"]["G"]["target"]
            pairs, err = sta_build_track_plan(erp, target_tracks)
            if err:
                print(f"\n== FBA {p['sn']} STA 快递号 ==  跳过: {err}")
                log.append({"sn": p["sn"], "type": "FBA", "step": "track", "result": f"跳过: {err}"})
            else:
                for sid, cid, tbl in pairs:
                    sta_body = {"sid": sid, "shipmentConfirmationId": cid, "trackBOList": tbl}
                    print(f"\n== FBA {p['sn']} STA 快递号 ({cid}) ==  {STA_UPDATE_TRACK}")
                    print(json.dumps(sta_body, ensure_ascii=False, indent=2))
                    if args.execute:
                        if input("写入以上快递号？输入 yes 确认: ").strip() != "yes":
                            log.append({"sn": p["sn"], "type": "FBA", "step": "track", "cid": cid, "result": "用户未确认"})
                            continue
                        resp = api_post(STA_UPDATE_TRACK, sta_body)
                        ok = str(resp.get("code")) in ("0", "200")
                        log.append({"sn": p["sn"], "type": "FBA", "step": "track", "cid": cid, "body": sta_body, "resp": resp, "ok": ok, "at": datetime.now().isoformat()})
                        print(f"返回: code={resp.get('code')} msg={resp.get('msg', resp.get('message', ''))}")
                        if not ok:
                            print("STA 接口返回错误。")
                            break
                        time.sleep(1)

        if not has_main and not has_fba_track:
            body = build_body(p, erp)
            path = WRITE_ENDPOINT[p["type"]]
            print(f"\n== {p['type']} {p['sn']} ==  {path}")
            print(json.dumps(body, ensure_ascii=False, indent=2))
            if args.execute:
                if input("写入以上内容？输入 yes 确认: ").strip() != "yes":
                    log.append({"sn": p["sn"], "result": "用户未确认"})
                    continue
                resp = api_post(path, body)
                ok = str(resp.get("code")) in ("0", "200")
                log.append({"sn": p["sn"], "type": p["type"], "body": body, "resp": resp, "ok": ok, "at": datetime.now().isoformat()})
                print(f"返回: code={resp.get('code')} msg={resp.get('msg')}")
                if not ok:
                    print("接口返回错误，停止后续写入。")
                    break
                time.sleep(RATE_SLEEP[p["type"]])

    out = args.plan.replace(".json", "_write_log.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
    print(f"\n写入日志: {out}（{len(log)} 条）；仅预览模式未写入" if not args.execute else f"\n写入日志: {out}")


# ---------------------------------------------------------------- read (直连 OpenAPI)

def _fba_from_mws(item):
    head = item.get("head_logistics_list") or {}
    tracks = [t.get("tracking_no") for t in head.get("track_list") or [] if t.get("tracking_no")]
    fee = (head.get("actual_expenses_list") or {}).get("logistics_fee")
    fba_shipments = []
    seen_ship = set()
    for it in item.get("items", []):
        ship_id = it.get("shipment_id", "")
        sid = it.get("sid")
        if ship_id and ship_id not in seen_ship:
            seen_ship.add(ship_id)
            fba_shipments.append({"shipmentConfirmationId": ship_id, "sid": sid})
    return {
        "tracking_number": head.get("logistics_tracking_number") or "",
        "provider_name": item.get("logistics_provider_name") or "",
        "channel_name": item.get("logistics_channel_name") or "",
        "tracking_list": tracks,
        "fee": fee or "",
        "fba_shipments": fba_shipments,
    }


def _ows_from_detail(d):
    li = d.get("logisticsInfo") or {}
    hi = li.get("head_logistics_info") or {}
    fee = next((f.get("logistics_fee") for f in li.get("head_logistics_fee_info") or [] if str(f.get("fee_type")) == "2"), "")
    tracks = [t.get("tracking_no") for t in li.get("head_logistics_tracking_info") or [] if t.get("tracking_no")]
    return {
        "tracking_number": hi.get("logistics_tracking_number") or "",
        "provider_name": hi.get("logistics_provider_name") or "",
        "channel_name": hi.get("logistics_channel_name") or "",
        "tracking_list": tracks,
        "fee": fee or "",
    }


def _fbt_from_list(sn, lst):
    item = next((x for x in lst if x.get("shippingListCode") == sn), lst[0] if lst else None)
    if item is None:
        return None
    details = item.get("logisticsDetails") or []
    total = round(sum(float(x.get("transportationCost") or 0) for x in details), 2)
    return {
        "tracking_number": (details[0].get("logisticsNumber") or "") if details else "",
        "provider_name": item.get("logisticsProviderName") or PROVIDER_NAMES.get(str(item.get("logisticsProviderId")), ""),
        "channel_name": item.get("logisticsChannelName") or "",
        "fee": f"{total:.2f}" if details else "",
        "logisticsInfo": [{"logisticsNumber": x.get("logisticsNumber") or "",
                           "trackingNumber": x.get("trackingNumber") or "",
                           "transportationCost": x.get("transportationCost") or "",
                           "transportationCurrency": x.get("transportationCurrency") or "CNY"} for x in details],
    }


def cmd_read(args):
    if not APP_ID or not APP_SECRET:
        sys.exit("缺少环境变量 LINGXING_APP_ID / LINGXING_APP_SECRET")
    with open(args.groups, encoding="utf-8") as f:
        groups = json.load(f)["groups"]
    out = {"FBA": {}, "OWS": {}, "FBT": {}}
    fba = [sn for sn, g in groups.items() if g["type"] == "FBA"]
    for i in range(0, len(fba), 50):
        chunk = fba[i:i + 50]
        resp = api_post("/erp/sc/routing/storage/shipment/getInboundShipmentListMwsDetailList",
                        {"shipment_sn_arr": chunk})
        items = resp.get("data") or []
        by_sn = {x.get("shipment_sn"): x for x in items}
        for sn in chunk:
            if sn in by_sn:
                out["FBA"][sn] = _fba_from_mws(by_sn[sn])
            else:
                print(f"[读取失败] FBA {sn}: 接口未返回")
        time.sleep(RATE_SLEEP["FBA"])
    for sn in [sn for sn, g in groups.items() if g["type"] == "OWS"]:
        resp = api_post("/basicOpen/overSeaWarehouse/stockOrder/detail", {"overseas_order_no": sn})
        if resp.get("data"):
            out["OWS"][sn] = _ows_from_detail(resp["data"])
        else:
            print(f"[读取失败] OWS {sn}: {resp.get('msg')}")
        time.sleep(RATE_SLEEP["OWS"])
    for sn in [sn for sn, g in groups.items() if g["type"] == "FBT"]:
        resp = api_post("/basicOpen/multiplatform/query/shippingList",
                        {"platformCodes": ["10011"], "searchField": 2, "searchSingleValue": sn, "length": 20, "offset": 0})
        rec = _fbt_from_list(sn, (resp.get("data") or {}).get("list") or [])
        if rec:
            out["FBT"][sn] = rec
        else:
            print(f"[读取失败] FBT {sn}")
        time.sleep(RATE_SLEEP["FBT"])
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"已读取 FBA {len(out['FBA'])} / OWS {len(out['OWS'])} / FBT {len(out['FBT'])} -> {args.out}")


# ---------------------------------------------------------------- verify

def cmd_verify(args):
    with open(args.plan, encoding="utf-8") as f:
        plans = json.load(f)["plans"]
    with open(args.erp_after, encoding="utf-8") as f:
        after = json.load(f)
    bad = 0
    for p in plans:
        if p["sn"] not in (args.sn or [p["sn"] for p in plans]):
            continue
        cur = after.get(p["type"], {}).get(p["sn"])
        if cur is None:
            print(f"[缺] {p['type']} {p['sn']} 未读取到写入后现值")
            bad += 1
            continue
        for k, v in p["fields"].items():
            if v["action"] not in ("写入", "覆盖"):
                continue
            if k == "F":
                got = cur.get("tracking_number", "")
                ok = got == v["target"]
            elif k == "I":
                ok = cur.get("provider_name", "") == v["target"]
                got = cur.get("provider_name", "")
            elif k == "H":
                ok = cur.get("channel_name", "") == v["target"]
                got = cur.get("channel_name", "")
            elif k == "G":
                if p["type"] == "FBT":
                    got = [i.get("trackingNumber") for i in cur.get("logisticsInfo") or [] if i.get("trackingNumber")]
                else:
                    got = cur.get("tracking_list") or []
                ok = set(v["target"]) <= set(got)
            elif k == "Q":
                ok = str(cur.get("fee") or "") not in UNSET and abs(float(cur.get("fee")) - float(v["target"])) < 0.005
                got = cur.get("fee")
            else:
                continue
            if not ok:
                bad += 1
            print(f"[{'通过' if ok else '失败'}] {p['type']} {p['sn']} {k}: 期望 {v['target']} 实际 {got}")
    print(f"\n验证失败 {bad} 项")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("parse")
    p.add_argument("--xlsx", required=True)
    p.add_argument("--out", default="groups.json")

    p = sub.add_parser("read", help="直连 OpenAPI 读取 ERP 现值（只读）")
    p.add_argument("--groups", default="groups.json")
    p.add_argument("--out", default="erp.json")

    p = sub.add_parser("plan")
    p.add_argument("--groups", default="groups.json")
    p.add_argument("--erp", required=True)
    p.add_argument("--out", default="plan.json")

    p = sub.add_parser("write")
    p.add_argument("--plan", default="plan.json")
    p.add_argument("--groups", default="groups.json")
    p.add_argument("--erp", required=True)
    p.add_argument("--sn", nargs="*")
    p.add_argument("--execute", action="store_true", help="真正写入；不加则只打印请求体")

    p = sub.add_parser("verify")
    p.add_argument("--plan", default="plan.json")
    p.add_argument("--erp-after", required=True)
    p.add_argument("--sn", nargs="*")

    args = ap.parse_args()
    if args.cmd == "parse":
        res = parse_xlsx(args.xlsx)
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=2)
        counts = {}
        for g in res["groups"].values():
            counts[g["type"]] = counts.get(g["type"], 0) + 1
        print(f"已解析 {len(res['groups'])} 个备货单 {counts} -> {args.out}；表格问题 {len(res['issues'])} 条")
    elif args.cmd == "read":
        cmd_read(args)
    elif args.cmd == "plan":
        cmd_plan(args)
    elif args.cmd == "write":
        cmd_write(args)
    elif args.cmd == "verify":
        cmd_verify(args)


if __name__ == "__main__":
    main()
