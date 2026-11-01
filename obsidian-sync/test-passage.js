/* v16 冒烟：短文记词（每组 30 词一篇小短文 · 覆盖率 · 视图 · 已读 · 改写） */
const fs = require('fs');

const PAGE = 'C:/Users/24277/WorkBuddy/2026-10-17-16-23-57/index.html';
const html = fs.readFileSync(PAGE, 'utf8');

const seedM = html.match(/<script[^>]*id="obs-seed"[^>]*>([\s\S]*?)<\/script>/);
const SEED = seedM ? seedM[1].trim() : '';
const pseedM = html.match(/<script[^>]*id="passage-seed"[^>]*>([\s\S]*?)<\/script>/);
const PSEED = pseedM ? pseedM[1].trim() : '';
const blocks = [...html.matchAll(/<script(?![^>]*application\/json)[^>]*>([\s\S]*?)<\/script>/g)].map(m => m[1]);
const MAIN = blocks.sort((a, b) => b.length - a.length)[0];

function mkClassList() {
  const set = new Set();
  return {
    add(...c) { c.forEach(x => set.add(x)) },
    remove(...c) { c.forEach(x => set.delete(x)) },
    contains(c) { return set.has(c) },
    toggle(c, force) {
      if (force === undefined) { set.has(c) ? set.delete(c) : set.add(c); return set.has(c) }
      force ? set.add(c) : set.delete(c); return !!force;
    },
    toString() { return [...set].join(' ') }, _set: set
  };
}
function mkEl(id) {
  const el = {
    id, _html: '', textContent: (id === 'obs-seed' ? SEED : id === 'passage-seed' ? PSEED : ''),
    value: '', type: '', accept: '', files: null, style: {}, dataset: {}, children: [], options: [],
    classList: mkClassList(),
    get innerHTML() { return this._html },
    set innerHTML(v) { this._html = String(v) },
    get className() { return this.classList.toString() },
    set className(v) { this.classList._set.clear(); String(v).split(/\s+/).filter(Boolean).forEach(c => this.classList._set.add(c)) },
    appendChild(c) { this.children.push(c); c.parentNode = this; return c },
    removeChild() {}, remove() {}, setAttribute() {}, getAttribute(k) { return this['_a_' + k] || null },
    addEventListener(k, fn) { (this._ev = this._ev || {})[k] = fn },
    removeEventListener() {}, focus() {}, click() {}, reset() {}, select() {},
    querySelector() { return null }, querySelectorAll() { return [] },
    insertAdjacentHTML() {}, scrollIntoView() {}
  };
  return el;
}
const els = new Map();
const document = {
  getElementById(id) { if (!els.has(id)) els.set(id, mkEl(id)); return els.get(id) },
  querySelector() { return null },
  querySelectorAll() { return [] },
  createElement() { return mkEl('created') },
  execCommand() {
    const kids = document.body.children;
    const ta = kids[kids.length - 1];
    if (ta && ta.value) globalThis.__copied = ta.value;
    return true;
  },
  addEventListener() {},
  body: mkEl('body'), documentElement: mkEl('html'), head: mkEl('head')
};
const store = new Map();
const localStorage = {
  getItem: k => (store.has(k) ? store.get(k) : null),
  setItem: (k, v) => store.set(k, String(v)),
  removeItem: k => store.delete(k), clear: () => store.clear()
};
class FakeDate extends Date {
  constructor(...args) { if (args.length === 0) super('2026-10-20T16:00:00+08:00'); else super(...args); }
  static now() { return Date.parse('2026-10-20T16:00:00+08:00'); }
}
globalThis.__copied = '';
globalThis.Date = FakeDate;
globalThis.window = { addEventListener() {}, removeEventListener() {}, location: { href: 'https://www.workbuddy.cn/x', hostname: 'www.workbuddy.cn', port: '', host: 'www.workbuddy.cn', protocol: 'https:' } };
globalThis.document = document;
globalThis.localStorage = localStorage;
globalThis.location = globalThis.window.location;
globalThis.fetch = () => Promise.reject(new TypeError('Failed to fetch'));
globalThis.URL.createObjectURL = () => 'blob:x';
globalThis.alert = () => {}; globalThis.prompt = () => null; globalThis.confirm = () => true;
globalThis.navigator = { clipboard: { writeText: t => { globalThis.__copied = t; return Promise.resolve() } } };

const runner = new Function('window', 'document', 'localStorage', 'fetch', 'alert', 'prompt', 'confirm', 'navigator',
  MAIN + `\n;globalThis.__api=function(){return {
    DB:DB, PS:PS, psSeed:psSeed, psGroups:psGroups, psWordsOf:psWordsOf, psGet:psGet, psMissing:psMissing,
    psMatch:psMatch, psHi:psHi, renderPassage:renderPassage, psPick:psPick, psSetView:psSetView,
    psMarkRead:psMarkRead, psReadToday:psReadToday, psReadTotal:psReadTotal, psCopyPrompt:psCopyPrompt,
    psSaveEdit:psSaveEdit, psOpenEdit:psOpenEdit, psWord:psWord, psIsRead:psIsRead, obsWords:()=>OBS.words
  }};`);
runner(globalThis.window, document, localStorage, globalThis.fetch, globalThis.alert, globalThis.prompt, globalThis.confirm, globalThis.navigator);

const A = globalThis.__api();
let pass = 0, fail = 0;
const ok = (c, m) => { if (c) { pass++; console.log('✅ ' + m) } else { fail++; console.error('❌ ' + m) } };
const el = id => document.getElementById(id);

/* ---------- 1. 内置短文 ---------- */
const seed = A.psSeed();
const groups = A.psGroups();
ok(groups.length === 11, '词表 11 组（' + groups.join(',') + '）');
ok(seed.length === 11, '内置短文 11 篇（' + seed.length + '）');
ok(seed.every(p => p.title && p.en && p.zh && p.hook), '每篇都有标题 / 英文 / 中文 / 记忆钩子');
ok(seed.every(p => p.en.split(/\s+/).length >= 180), '每篇英文都在 180 词以上（最短 ' +
  Math.min(...seed.map(p => p.en.split(/\s+/).length)) + ' 词）');

/* ---------- 2. 覆盖率：每组 30 词必须全出现 ---------- */
let badG = [];
groups.forEach(g => {
  const p = A.psGet(g), ws = A.psWordsOf(g);
  const miss = A.psMissing(p, ws);
  if (ws.length !== 30 || miss.length) badG.push(g + '(缺 ' + miss.join(',') + ')');
});
ok(badG.length === 0, '11 篇全部 30/30 覆盖本组词' + (badG.length ? ' 问题组：' + badG.join('；') : ''));

/* ---------- 3. 词形匹配规则 ---------- */
ok(A.psMatch('motivated', 'motivate'), '词形：motivated → motivate');
ok(A.psMatch('decorating', 'decorate'), '词形：decorating → decorate');
ok(A.psMatch('fireworks', 'firework'), '词形：fireworks → firework');
ok(A.psMatch('regulations', 'regulation'), '词形：regulations → regulation');
ok(!A.psMatch('cared', 'career'), '不误判：cared ≠ career');
ok(!A.psMatch('prisoner', 'prison'), '严格：prisoner ≠ prison（两词都得在文里出现）');

/* ---------- 4. 渲染 ---------- */
A.PS.cur = 1;
A.renderPassage();
const body = el('psBody').innerHTML;
ok(/The Green School/.test(body), '第 1 组渲染出标题');
ok(/第 1 组/.test(body), '标题旁有组次徽标');
ok(/30\/30/.test(body), '标题旁显示 30/30 覆盖');
ok(/class="pw"/.test(body), '正文里目标词被高亮（class="pw"）');
ok(/💡/.test(body), '正文上方有记忆钩子');
ok(/我们学校上学期启动了一个绿色项目/.test(body) && body.split('<p>').length > 8, '中文对照已渲染（段落齐全）');
ok(el('psCover').innerHTML.split('ps-cw').length - 1 === 30, '覆盖核对区 30 个词 chip');
ok(/30\/30 词在文中出现/.test(el('psCoverCnt').textContent), '覆盖统计文案正确');

/* ---------- 5. 选组 ---------- */
A.psPick(11);
ok(/The Fake Bag/.test(el('psBody').innerHTML), '切到第 11 组 → 换成本组短文');
ok(A.PS.cur === 11, '当前组 = 11');
ok(el('psChips').innerHTML.split('chip').length - 1 === 11, '组次 chips 共 11 个');

/* ---------- 6. 视图切换 ---------- */
A.psSetView('en');
ok(el('psZh').style.display === 'none' && !el('psEn').style.display, '只看英文 → 中文隐藏');
A.psSetView('zh');
ok(el('psEn').style.display === 'none', '只看中文 → 英文隐藏');
A.psSetView('both');
ok(!el('psEn').style.display && !el('psZh').style.display, '中英对照 → 两栏都显示');
ok(el('psVBoth').classList.contains('on') && !el('psVEn').classList.contains('on'), '视图按钮高亮跟随');

/* ---------- 7. 已读标记 ---------- */
A.psPick(3);
ok(A.psReadToday() === 0, '初始今日精读 0 篇');
A.psMarkRead();
ok(A.psReadToday() === 1 && A.psReadTotal() === 1, '标记已读 → 今日 1 篇 / 累计 1 篇');
ok(A.psIsRead(3), '第 3 组记为已读');
ok(el('psChips').innerHTML.indexOf('第 3 组 ✓') >= 0, '组次 chip 出现 ✓');
ok(/已读/.test(el('psReadBtn').textContent), '按钮变成「已读」');
A.psMarkRead();
ok(A.psReadToday() === 0 && !A.psIsRead(3), '再点一次 → 取消已读');

/* ---------- 8. 点词看释义 ---------- */
A.psWord('curriculum');
const wb = el('psWordBox').innerHTML;
ok(el('psWordBox').style.display === 'block', '点词后弹出释义条');
ok(/课程体系/.test(wb) && /第 1 组/.test(wb), '释义条含中文与组次');

/* ---------- 9. 复制写作提示词 ---------- */
A.psPick(10);
globalThis.__copied = '';
A.psCopyPrompt();
ok(globalThis.__copied.length > 300, '提示词已复制（' + globalThis.__copied.length + ' 字）');
ok(/覆盖全部 30 个词/.test(globalThis.__copied), '提示词写明 30 词全覆盖');
const words10 = A.psWordsOf(10);
ok(words10.every(w => globalThis.__copied.includes(w)), '提示词里 30 个词一个不少');

/* ---------- 10. 改写保存 ---------- */
A.psPick(11);
A.psOpenEdit();
ok(el('psEditBox').style.display === 'block', '编辑框打开');
el('psETitle').value = 'A New Fake Bag Story';
el('psEEn').value = 'A journalist received an anonymous message about a fake bag. '.repeat(3);
el('psEZh').value = '一位记者收到关于假包的匿名消息。';
A.psSaveEdit();
ok(el('psEditBox').style.display === 'none', '保存后编辑框收起');
ok(!!A.DB.passages[11], '改写存进 DB.passages（本机覆盖）');
ok(/A New Fake Bag Story/.test(el('psBody').innerHTML), '页面已显示改后的标题');
ok(/漏 \d+ 词/.test(el('psBody').innerHTML), '改写后覆盖率不足会标红提示漏词');
ok(/第 11 组/.test(el('psBody').innerHTML), '改写后组次徽标仍在');
delete A.DB.passages[11];

/* ---------- 10.5 新组还没短文 → 空态 + 提示词兜底 ---------- */
A.obsWords().push({ w: 'zzznew', ipa: 'z', pos: 'n.', zh: '新词', grp: 12, gdate: '2026-10-21', cat: '测试', chunk: '', mn: '' });
ok(A.psGroups().indexOf(12) >= 0, '新加的第 12 组出现在组次列表里');
ok(A.psGet(12) === null, '第 12 组还没有短文');
A.psPick(12);
ok(/还没有短文/.test(el('psBody').innerHTML), '没有短文的组 → 显示空态说明');
ok(/ps-nop/.test(el('psChips').innerHTML), '没有短文的组 chip 标为虚线');
globalThis.__copied = '';
A.psCopyPrompt();
ok(/zzznew/.test(globalThis.__copied), '空态下也能复制本组词表（提示词含新词）');
A.obsWords().pop();
A.PS.cur = 0;

/* ---------- 11. 页面结构 ---------- */
ok(/id="passage-seed"/.test(html), '页面内置 passage-seed');
ok(/id="psBody"/.test(html) && /id="psChips"/.test(html), '短文页 DOM 就位');
ok(!/id="sntList"/.test(html), '长难句卡片已移除');
ok(/id="p-snt"/.test(html) && /📝 短文记词/.test(html), '原长难句页位置挂的是「短文记词」');
ok(/短文精读/.test(html), '今日目标已改为「短文精读」');

console.log(`\n${fail === 0 ? '🎉' : '⚠️'} 短文记词：${pass} 通过 / ${fail} 失败`);
process.exit(fail === 0 ? 0 : 1);
