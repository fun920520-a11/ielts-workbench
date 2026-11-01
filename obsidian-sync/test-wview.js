/* v15 冒烟：单词列表「英文 / 中文」显示开关 + 单格揭示 */
const fs = require('fs');

const PAGE = 'C:/Users/24277/WorkBuddy/2026-10-17-16-23-57/index.html';
const html = fs.readFileSync(PAGE, 'utf8');

const seedM = html.match(/<script[^>]*id="obs-seed"[^>]*>([\s\S]*?)<\/script>/);
const SEED = seedM ? seedM[1].trim() : '';
const blocks = [...html.matchAll(/<script(?![^>]*application\/json)[^>]*>([\s\S]*?)<\/script>/g)].map(m => m[1]);
const MAIN = blocks.sort((a, b) => b.length - a.length)[0];

/* ---------- 带状态的 classList 桩 ---------- */
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
    toString() { return [...set].join(' ') },
    _set: set
  };
}
function mkEl(id) {
  const el = {
    id, _html: '', textContent: id === 'obs-seed' ? SEED : '', value: '', type: '', accept: '', files: null,
    style: {}, dataset: {}, children: [], options: [], classList: mkClassList(),
    get innerHTML() { return this._html },
    set innerHTML(v) { this._html = String(v) },
    get className() { return this.classList.toString() },
    set className(v) { this.classList._set.clear(); String(v).split(/\s+/).filter(Boolean).forEach(c => this.classList._set.add(c)) },
    appendChild(c) { this.children.push(c); c.parentNode = this; return c },
    removeChild() {}, remove() {}, setAttribute() {}, getAttribute() { return null },
    addEventListener(k, fn) { (this._ev = this._ev || {})[k] = fn },
    removeEventListener() {}, focus() {}, click() {}, reset() {},
    querySelector() { return null }, querySelectorAll() { return [] },
    insertAdjacentHTML() {}, scrollIntoView() {}
  };
  el.classList._set.clear();
  return el;
}
const els = new Map();
const maskNodes = [];          // 所有「可遮盖」假节点：{classList, parentNode}
const document = {
  getElementById(id) { if (!els.has(id)) els.set(id, mkEl(id)); return els.get(id) },
  querySelector() { return null },
  querySelectorAll(sel) {
    if (sel === '#wList .maskable.peek') return maskNodes.filter(n => n.classList.contains('peek'));
    if (sel === '#wList .maskable') return maskNodes.slice();
    return [];
  },
  createElement() { return mkEl('created') },
  addEventListener() {},
  body: mkEl('body'), documentElement: mkEl('html'), head: mkEl('head')
};
document.getElementById('wList').querySelectorAll = document.querySelectorAll;

const store = new Map();
const localStorage = {
  getItem: k => (store.has(k) ? store.get(k) : null),
  setItem: (k, v) => store.set(k, String(v)),
  removeItem: k => store.delete(k), clear: () => store.clear()
};

class FakeDate extends Date {
  constructor(...args) { if (args.length === 0) super('2026-10-20T10:00:00+08:00'); else super(...args); }
  static now() { return Date.parse('2026-10-20T10:00:00+08:00'); }
}
globalThis.Date = FakeDate;
globalThis.window = { addEventListener() {}, removeEventListener() {}, location: { href: 'https://www.workbuddy.cn/x', hostname: 'www.workbuddy.cn', port: '', host: 'www.workbuddy.cn', protocol: 'https:' } };
globalThis.document = document;
globalThis.localStorage = localStorage;
globalThis.location = globalThis.window.location;
globalThis.fetch = () => Promise.reject(new TypeError('Failed to fetch'));
globalThis.URL.createObjectURL = () => 'blob:x';
globalThis.alert = () => {}; globalThis.prompt = () => null; globalThis.confirm = () => true;
globalThis.navigator = { clipboard: { writeText: () => Promise.resolve() } };

const runner = new Function('window', 'document', 'localStorage', 'fetch', 'alert', 'prompt', 'confirm', 'navigator',
  MAIN + `\n;globalThis.__api=function(){return {
    WV:WV, wvToggle:wvToggle, wvReset:wvReset, wvPeek:wvPeek, wvPaint:wvPaint,
    renderWList:renderWList, setWGrp:setWGrp, wvHint:wvHint, obsWords:()=>OBS.words
  }};`);
runner(globalThis.window, document, localStorage, globalThis.fetch, globalThis.alert, globalThis.prompt, globalThis.confirm, globalThis.navigator);

const A = globalThis.__api();
let pass = 0, fail = 0;
const ok = (cond, msg) => { if (cond) { pass++; console.log('✅ ' + msg) } else { fail++; console.error('❌ ' + msg) } };

const wList = document.getElementById('wList');
const el = id => document.getElementById(id);
const saveKey = 'ielts_wview_v1';
const countOf = (hay, needle) => (hay.split(needle).length - 1);

/* ---------- 1. 默认：两列都显示 ---------- */
ok(A.WV.en === true && A.WV.zh === true, '默认英文 / 中文都显示');
A.renderWList();
ok(!wList.classList.contains('mask-en') && !wList.classList.contains('mask-zh'), '默认 #wList 没有遮罩 class');
ok(countOf(wList.innerHTML, 'class="w maskable"') > 0, '单词列带 maskable 标记');
ok(countOf(wList.innerHTML, 'class="ipa maskable"') > 0, '音标列带 maskable 标记');
ok(countOf(wList.innerHTML, 'class="m maskable"') > 0, '中文列带 maskable 标记');
ok(countOf(wList.innerHTML, 'class="w maskable"') === countOf(wList.innerHTML, 'class="m maskable"'),
  '英中两列数量一致（' + countOf(wList.innerHTML, 'class="w maskable"') + ' 行）');
ok(/两列都显示/.test(el('wvHint').textContent), '提示文案说明可以遮住某一列');
ok(el('wvEn').innerHTML.indexOf('👁') === 0 && el('wvZh').innerHTML.indexOf('👁') === 0, '两个开关初始都是「眼睛」图标');
ok(el('wvEn').classList.contains('on') && el('wvZh').classList.contains('on'), '两个开关初始都是选中态');

/* ---------- 2. 隐藏中文 ---------- */
A.wvToggle('zh');
ok(wList.classList.contains('mask-zh') && !wList.classList.contains('mask-en'), '隐藏中文 → 只加 mask-zh');
ok(el('wvZh').innerHTML.indexOf('🙈') === 0 && !el('wvZh').classList.contains('on'), '中文开关变「捂眼」并取消选中');
ok(el('wvEn').classList.contains('on'), '英文开关不受影响');
ok(/已隐藏中文/.test(el('wvHint').textContent), '提示文案：已隐藏中文');
ok(JSON.parse(store.get(saveKey)).zh === false, '隐藏状态写进 localStorage');

/* ---------- 3. 再隐藏英文 ---------- */
A.wvToggle('en');
ok(wList.classList.contains('mask-en') && wList.classList.contains('mask-zh'), '中英都隐藏 → 两个 class 都在');
ok(/已隐藏英文 和 中文/.test(el('wvHint').textContent), '提示文案：英文和中文都隐藏');

/* ---------- 4. 恢复英文 ---------- */
A.wvToggle('en');
ok(!wList.classList.contains('mask-en') && wList.classList.contains('mask-zh'), '只恢复英文 → 中文仍遮着');
ok(JSON.parse(store.get(saveKey)).en === true, 'localStorage 同步为 en=true / zh=false');

/* ---------- 5. 单格揭示（点一下只看这一格） ---------- */
const node = { classList: mkClassList(), parentNode: wList };
node.classList.add('m', 'maskable');      // 中文列当前是隐藏的
maskNodes.push(node);
A.wvPeek({ target: node });
ok(node.classList.contains('peek'), '点被遮住的格子 → 单独揭示（peek）');
ok(/已揭示 1 格/.test(el('wvHint').textContent), '提示文案统计已揭示格数');
ok(el('wvReset').style.display === 'inline-block', '出现「重新遮盖」按钮');

/* 已显示的列点一下不该有反应 */
const zhNode = { classList: mkClassList(), parentNode: wList };
zhNode.classList.add('w', 'maskable');   // 英文当前是显示状态
maskNodes.push(zhNode);
A.wvPeek({ target: zhNode });
ok(!zhNode.classList.contains('peek'), '没被遮住的格子点了不揭示');

/* 点按钮不该被当成格子 */
const btn = { classList: mkClassList(), parentNode: wList };
btn.classList.add('btn-o');
maskNodes.push(btn);
A.wvPeek({ target: btn });
ok(!btn.classList.contains('peek'), '点按钮不触发揭示');

/* ---------- 6. 重新遮盖 ---------- */
A.wvReset();
ok(!node.classList.contains('peek') && maskNodes.filter(n => n.classList.contains('peek')).length === 0, '重新遮盖清空所有 peek');
ok(el('wvReset').style.display === 'none', '没有 peek 时「重新遮盖」按钮隐藏');

/* ---------- 7. 重新渲染后遮罩仍在 ---------- */
A.renderWList();
ok(wList.classList.contains('mask-zh'), '重渲染后仍保持「隐藏中文」');
ok(el('wvZh').innerHTML.indexOf('🙈') === 0, '重渲染后开关状态也一致');

/* ---------- 8. 与搜索 / 分组筛选共存 ---------- */
el('wSearch').value = 'career';
A.renderWList();
ok(countOf(wList.innerHTML, 'class="wrow"') === 1 && /career/.test(wList.innerHTML), '遮罩时搜索仍能过滤（career 命中 1 行）');
ok(wList.classList.contains('mask-zh'), '搜索后遮罩没被重置');
el('wSearch').value = '';
A.setWGrp('2');
const rows2 = countOf(wList.innerHTML, 'class="wrow"'), tags2 = countOf(wList.innerHTML, '第 2 组');
const leak = ['第 1 组', '第 3 组', '第 10 组'].filter(t => wList.innerHTML.includes(t));
ok(rows2 === 30 && tags2 >= 30 && leak.length === 0,
  '遮罩时选组仍正确（' + rows2 + ' 行 / ' + tags2 + ' 处组次标记，无串组）');
ok(countOf(wList.innerHTML, 'class="m maskable"') === 30, '第 2 组 30 行的中文列都可遮盖');
A.setWGrp('all');

/* ---------- 9. 恢复两列显示 ---------- */
A.wvToggle('zh');
ok(!wList.classList.contains('mask-zh') && !wList.classList.contains('mask-en'), '两个开关都开回来 → 无遮罩');
ok(/两列都显示/.test(el('wvHint').textContent), '提示文案回到默认');
ok(JSON.parse(store.get(saveKey)).zh === true, 'localStorage 记录全显示');
ok(countOf(wList.innerHTML, 'maskable') === 90 * 1 || countOf(wList.innerHTML, 'maskable') > 0, '渲染行里仍有 maskable 标记（' + countOf(wList.innerHTML, 'maskable') + '）');

/* ---------- 10. 页面里真的有三件套 ---------- */
ok(/id="wvEn"/.test(html) && /id="wvZh"/.test(html) && /id="wvReset"/.test(html), '页面存在「英文 / 中文 / 重新遮盖」三个控件');
ok(/addEventListener\('click',wvPeek\)/.test(html), '列表容器挂了点击揭示的监听');

console.log(`\n${fail === 0 ? '🎉' : '⚠️'} 中英显示开关：${pass} 通过 / ${fail} 失败`);
process.exit(fail === 0 ? 0 : 1);
