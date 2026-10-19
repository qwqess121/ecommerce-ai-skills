// 用法：node build.js <报告目录>
// 生成 <报告目录>/report.html。可以只有一个模块，也可以是 1–5 个模块全部。
//   sections.json  —— convert.js 生成，只包含实际存在的模块
//   overview.html  —— 可选：总览页正文（有则作为第 00 页）
//   overview.json  —— 可选：页面标题与品牌信息（缺省时由模块标题推断）
// 结构按参考报告 Xk3D：左侧索引 + 每页一个 section.page + 页末翻页导航。
const fs = require('fs');
const path = require('path');

const dir = process.argv[2];
if (!dir) {
  console.error('用法：node build.js <报告目录>');
  process.exit(1);
}

const exists = (name) => fs.existsSync(path.join(dir, name));
const read = (name) => fs.readFileSync(path.join(dir, name), 'utf8');

if (!exists('sections.json')) {
  console.error('缺少 sections.json，请先运行 node convert.js <报告目录>');
  process.exit(1);
}
const sections = JSON.parse(read('sections.json'));

// 页序固定：00 总览（可选），然后模块 m1–m5（只取实际存在的）
const MODULE_LABELS = {
  m1: '产品开发',
  m2: '竞品销售策略',
  m3: 'Listing 诊断',
  m4: '广告策略',
  m5: '内容生产',
};
const pages = [];
if (exists('overview.html')) {
  pages.push({ id: 'm0', label: '总览', html: read('overview.html') });
}
for (const id of ['m1', 'm2', 'm3', 'm4', 'm5']) {
  if (typeof sections[id] === 'string' && sections[id].trim()) {
    pages.push({ id, label: MODULE_LABELS[id], html: sections[id] });
  }
}
if (pages.length === 0) {
  console.error('没有可渲染的页面：报告目录内既没有 overview.html，也没有模块内容。');
  process.exit(1);
}

// 没有总览页时，在第一个模块页的 H1 之后放模块卡片（链接 #m1–#m5），不生成总览页。
// 卡片文字取自各模块的第一个 H2，不另外编造内容；只有一个模块时不生成。
if (!exists('overview.html') && pages.length > 1) {
  const stripTags = (t) => t.replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim();
  const cards = pages
    .filter((p) => /^m[1-5]$/.test(p.id))
    .map((p) => {
      const h2s = [...p.html.matchAll(/<h2[^>]*>([\s\S]*?)<\/h2>/gi)].map((m) => stripTags(m[1]));
      const first = h2s[0] || '';
      return [
        `  <a class="modcard" href="#${p.id}">`,
        `    <span class="modcard-num">0${p.id.slice(1)}</span>`,
        `    <h3>${p.label}</h3>`,
        `    <p>${first}</p>`,
        `    <span class="modcard-tag">共 ${h2s.length} 节</span>`,
        '  </a>',
      ].join('\n');
    })
    .join('\n');
  const grid = `\n<div class="mod-grid" aria-label="模块导航">\n${cards}\n</div>\n`;
  const first = pages[0];
  const h1End = first.html.search(/<\/h1>/i);
  if (h1End >= 0) {
    first.html = first.html.slice(0, h1End + 5) + grid + first.html.slice(h1End + 5);
  }
}

// 页标题与品牌信息：优先用 overview.json；没有则从第一页的 H1 推断
let meta = {};
if (exists('overview.json')) {
  meta = JSON.parse(read('overview.json'));
}
const firstH1 = (() => {
  const m = pages[0].html.match(/<h1[^>]*>([\s\S]*?)<\/h1>/i);
  return m ? m[1].replace(/<[^>]+>/g, '').trim() : '';
})();
const title = meta.title || firstH1 || '分析报告';
const brandName = meta.brand_name || '分析报告';
const brandSub = meta.brand_sub || '';

const numOf = (id) => (id === 'm0' ? '00' : `0${id.slice(1)}`);

const navHtml = pages
  .map((p) => `  <a href="#${p.id}">${numOf(p.id)} ${p.label}</a>`)
  .join('\n');

const pagerHtml = (i) => {
  const prev = i > 0 ? pages[i - 1] : null;
  const next = i < pages.length - 1 ? pages[i + 1] : null;
  const prevLink = prev
    ? `<a href="#${prev.id}" data-go="${prev.id}">← 上一页：${prev.label}</a>`
    : '<span></span>';
  const nextLink = next
    ? `<a href="#${next.id}" data-go="${next.id}">下一页：${next.label} →</a>`
    : '<span></span>';
  return `\n<nav class="pager" aria-label="翻页">${prevLink}<span>第 ${i + 1} / ${pages.length} 页</span>${nextLink}</nav>`;
};

const sectionsHtml = pages
  .map((p, i) => `<section id="${p.id}" class="page">\n${p.html}${pagerHtml(i)}\n</section>`)
  .join('\n');

const template = fs.readFileSync(path.join(__dirname, 'template.html'), 'utf8');

const page = template
  .replace('{{TITLE}}', () => title)
  .replace('{{BRAND_NAME}}', () => brandName)
  .replace('{{BRAND_SUB}}', () => brandSub)
  .replace('{{NAV}}', () => navHtml)
  .replace('{{SECTIONS}}', () => sectionsHtml);

fs.writeFileSync(path.join(dir, 'report.html'), page, 'utf8');
console.log(
  'built', path.join(dir, 'report.html'),
  '页面：' + pages.map((p) => p.id).join(', '),
  'size(KB)=', (Buffer.byteLength(page) / 1024).toFixed(1)
);
