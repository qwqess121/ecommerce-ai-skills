const { marked } = require('marked');
const fs = require('fs');
const path = require('path');

marked.setOptions({ gfm: true, breaks: false });

// 用法：node convert.js <报告目录>
// 报告目录内放 模块1-*.md ~ 模块5-*.md 中的任意几份（文件名前缀决定模块序号，其余文字不限）。
// 输出：<报告目录>/sections.json，供 build.js 使用。
const dir = process.argv[2];
if (!dir) {
  console.error('用法：node convert.js <报告目录>');
  process.exit(1);
}
const files = fs
  .readdirSync(dir)
  .map((name) => {
    const m = name.match(/^模块([1-5])-.*\.md$/);
    return m ? { id: `m${m[1]}`, file: name } : null;
  })
  .filter(Boolean)
  .sort((a, b) => a.id.localeCompare(b.id));
// 允许只有部分模块（1–5 份都可以）；至少要有一份模块 md
if (files.length === 0) {
  console.error('报告目录内没有模块 md。文件名须以 模块1-、模块2-…模块5- 开头。');
  process.exit(1);
}
console.log('模块：' + files.map((f) => f.id + ' ← ' + f.file).join('；'));

// 目录不再手抄：手写的目录文本经常在多轮编辑后和实际标题对不上（编号漂移/措辞不同步），
// 且原本就不是真链接，点了没反应。改成：构建脚本自动扫描全部二级标题（真正的编号大节），
// 生成锚点 id + 可点击目录，标题文字和目录文字永远来自同一处，不会再不同步。

function stripManualToc(raw) {
  // 删掉手写"本页目录/目录"标题后面那段纯文本列表，只留标题本身，位置留给自动生成的目录
  const lines = raw.split('\n');
  const out = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    const isTocHeading = /^#{2,3}\s*.*(本页目录|目录).*$/.test(line);
    out.push(line);
    i++;
    if (isTocHeading) {
      while (
        i < lines.length &&
        lines[i].trim() !== '' &&
        !/^#{1,6}\s/.test(lines[i]) &&
        !/^-{3,}\s*$/.test(lines[i])
      ) {
        i++;
      }
    }
  }
  return out.join('\n');
}

// ASIN / 品牌名自动跳转——扫描全部 5 份 md 的表格与行内写法，建立"品牌名 -> ASIN"映射，
// 报告里任何地方出现这个 ASIN 或品牌名，都自动加上指向该 Amazon 商品页的链接。
// 映射从当前文档内容里现场提取，不手工维护品牌清单——报告改版时不会跟着漂移失效。
function extractBrandAsinMap(rawTexts) {
  const asinSets = {}; // brand -> Set(asin)，同一品牌名如果对应多个不同 ASIN（多 SKU/多变体），判定为有歧义
  const addPair = (brandRaw, asin) => {
    if (!brandRaw || !asin) return;
    let brand = brandRaw
      .replace(/\[([^\]]+)\]\([^)]*\)/, '$1') // 去掉 markdown 链接语法，只留文字
      .replace(/\*\*/g, '')
      .split(/[（(]/)[0] // 去掉括注部分，如"AROIC（1周前上位）"只取"AROIC"
      .trim();
    if (brand.length < 3) return; // 太短的名字误伤风险高，跳过
    if (/^[-—/·全部本品真\d]/.test(brand)) return; // 过滤明显不是品牌名的表格占位内容
    if (!asinSets[brand]) asinSets[brand] = new Set();
    asinSets[brand].add(asin);
  };

  for (const raw of rawTexts) {
    const lines = raw.split('\n');
    // 1) 表格提取：表头含"ASIN"列 + "品牌"列的表格，逐行取 (品牌, ASIN) 对
    for (let i = 0; i < lines.length - 1; i++) {
      if (!lines[i].trim().startsWith('|')) continue;
      const sep = lines[i + 1] || '';
      if (!/^\|?\s*:?-+:?\s*\|/.test(sep.trim())) continue;
      const header = lines[i].split('|').map((s) => s.trim());
      const asinIdx = header.findIndex((h) => /^asin$/i.test(h));
      const brandIdx = header.findIndex((h) => /品牌/.test(h));
      if (asinIdx === -1 || brandIdx === -1) continue;
      for (let j = i + 2; j < lines.length; j++) {
        if (!lines[j].trim().startsWith('|')) break;
        const cells = lines[j].split('|').map((s) => s.trim());
        const asinMatch = (cells[asinIdx] || '').match(/B0[A-Z0-9]{8}/);
        if (!asinMatch) continue;
        addPair(cells[brandIdx], asinMatch[0]);
      }
    }
    // 2) 行内提取：正文里"品牌名（B0XXXXXXXX）"或"品牌名(B0XXXXXXXX)"这种写法
    const inlineRe = /([A-Za-z][A-Za-z0-9&' .]{1,28})[（(]\s*(B0[A-Z0-9]{8})\s*[)）]/g;
    let m;
    while ((m = inlineRe.exec(raw))) {
      addPair(m[1], m[2]);
    }
  }
  // 只保留"品牌名 -> 唯一 ASIN"的无歧义映射；同名对多个 ASIN 的（如本品自己"HoogaLife"有多个 SKU、
  // "drift"/"Febreze"有多个变体），品牌名本身不自动加链接，避免链去错的商品——ASIN 本身照样能点。
  const map = {};
  for (const [brand, set] of Object.entries(asinSets)) {
    if (set.size === 1) map[brand] = [...set][0];
  }
  return map;
}

const brandAsinMap = extractBrandAsinMap(
  files.map((f) => fs.readFileSync(path.join(dir, f.file), 'utf8'))
);
// 按品牌名长度从长到短排序，避免"CE CRAFT"被"CE"这种更短的名字先抢先匹配掉一部分
const brandNames = Object.keys(brandAsinMap).sort((a, b) => b.length - a.length);

function amazonLink(asin) {
  return `https://www.amazon.com/dp/${asin}`;
}

// 只处理 HTML 文本节点，不碰标签本身/属性——把字符串按"标签 vs 文本"切开，只对文本片段做替换；
// 已经在 <a>…</a> 内部的文字跳过（比如源 md 里本来就写了 [ASIN](https://...) 这种手写链接），
// 否则会在已有链接外面再包一层，出现 <a><a>…</a></a> 锚套锚。
function linkifyAsinsAndBrands(html) {
  let anchorDepth = 0;
  return html.replace(/(<a\b[^>]*>)|(<\/a>)|(<[^>]*>)|([^<]+)/g, (whole, aOpen, aClose, tag, text) => {
    if (aOpen) { anchorDepth++; return aOpen; }
    if (aClose) { anchorDepth = Math.max(0, anchorDepth - 1); return aClose; }
    if (tag) return tag;
    if (anchorDepth > 0) return text; // 已在链接内部，原样返回，不重复加链接
    let t = text;
    // 品牌名优先处理（更长、更具体），处理时跳过刚生成的 <a>…</a> 内部文字，用零宽断言不好做，
    // 改用先占位再回填的方式：品牌名替换生成的 <a> 用唯一占位符保护，最后统一替换回真实 HTML。
    const placeholders = [];
    const protect = (html_) => {
      placeholders.push(html_);
      return `\u0000${placeholders.length - 1}\u0000`;
    };
    for (const brand of brandNames) {
      if (t.indexOf(brand) === -1) continue;
      const esc = brand.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const re = new RegExp(`(^|[^A-Za-z0-9])(${esc})(?![A-Za-z0-9])`, 'g');
      t = t.replace(re, (_, pre, name) =>
        pre + protect(`<a href="${amazonLink(brandAsinMap[brand])}" target="_blank" rel="noopener" class="asin">${name}</a>`)
      );
    }
    t = t.replace(/\bB0[A-Z0-9]{8}\b/g, (asin) =>
      protect(`<a href="${amazonLink(asin)}" target="_blank" rel="noopener" class="asin">${asin}</a>`)
    );
    t = t.replace(/\u0000(\d+)\u0000/g, (_, idx) => placeholders[Number(idx)]);
    return t;
  });
}

const out = {};
for (const f of files) {
  const raw0 = fs.readFileSync(path.join(dir, f.file), 'utf8');
  const raw = stripManualToc(raw0);

  // 预扫描：按文档顺序收集全部二级标题（排除目录标题自身），确定目录条目和锚点 id
  const tokens = marked.lexer(raw);
  const headings = [];
  let counter = 0;
  for (const t of tokens) {
    if (t.type === 'heading' && t.depth === 2 && !/目录/.test(t.text)) {
      counter++;
      headings.push({ id: `${f.id}-h${counter}`, text: t.text });
    }
  }

  // 渲染：用完全相同的过滤条件 + 相同的遍历顺序给二级标题打 id，保证和上面扫描到的列表一一对应
  const renderer = new marked.Renderer();
  let counter2 = 0;
  renderer.heading = function (token) {
    const depth = token.depth;
    const text = this.parser.parseInline(token.tokens);
    if (depth === 2 && !/目录/.test(token.text)) {
      counter2++;
      return `<h2 id="${f.id}-h${counter2}">${text}</h2>\n`;
    }
    return `<h${depth}>${text}</h${depth}>\n`;
  };

  let html = marked.parse(raw, { renderer });
  html = linkifyAsinsAndBrands(html); // 目录还没拼进来，避免目录链接文字里再嵌一层 <a> 导致锚套锚

  const tocUl =
    '<ul class="toc-list">' +
    headings
      .map(
        (h) =>
          `<li><a href="#${h.id}" class="toc-link" data-module="${f.id}" data-target="${h.id}">${h.text}</a></li>`
      )
      .join('') +
    '</ul>';
  html = html.replace(/(<h[23]>[^<]*目录[^<]*<\/h[23]>)/, `$1${tocUl}`);

  // 表格统一包进 <div class="tablewrap">（参考报告 Xk3D 的写法）；先去掉已有包裹，避免重复
  html = html.replace(/<div class="tablewrap">\s*<table>/g, '<table>').replace(/<\/table>\s*<\/div>/g, '</table>');
  html = html.replace(/<table>/g, '<div class="tablewrap"><table>').replace(/<\/table>/g, '</table></div>');
  out[f.id] = html;
}

fs.writeFileSync(path.join(dir, 'sections.json'), JSON.stringify(out), 'utf8');
console.log('done', Object.keys(out).map((k) => k + ':' + out[k].length));
