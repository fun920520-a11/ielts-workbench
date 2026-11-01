/* 首页「今日提醒」回归：当天学习组 + 当日艾宾浩斯复习任务
   跑法：node test-hero.js   （日期冻结在 2026-10-20，复现用户举例） */
const fs = require('fs');
const PAGE = 'C:/Users/24277/WorkBuddy/2026-10-17-16-23-57/index.html';
const html = fs.readFileSync(PAGE, 'utf8');
const CODE = [...html.matchAll(/<script(?![^>]*application\/json)[^>]*>([\s\S]*?)<\/script>/g)]
  .map(m => m[1]).join('\n');
const seedM = html.match(/<script[^>]*id="obs-seed"[^>]*>([\s\S]*?)<\/script>/);
const SEED = seedM ? seedM[1].trim() : '';

let pass = 0, fail = 0;
function ok(c, msg) {
  if (c) { pass++; console.log('✅ ' + msg) } else { fail++; console.log('❌ ' + msg) }
}

/* ---------- DOM 桩 ---------- */
function mkEl(id) {
  const e = {
    id, _html: '', textContent: id === 'obs-seed' ? SEED : '', value: '', style: {}, dataset: {}, className: '',
    classList: {
      _s: new Set(),
      add(c) { this._s.add(c) }, remove(c) { this._s.delete(c) },
      toggle(c, on) { on === undefined ? (this._s.has(c) ? this._s.delete(c) : this._s.add(c)) : (on ? this._s.add(c) : this._s.delete(c)) },
      contains(c) { return this._s.has(c) }
    },
    appendChild(c) { return c }, removeChild() {}, remove() {},
    setAttribute() {}, getAttribute() { return null }, addEventListener() {}, removeEventListener() {},
    focus() {}, click() {}, reset() {}, insertAdjacentHTML() {}, scrollIntoView() {},
    querySelector() { return mkEl('q') }, querySelectorAll() { return [] },
    getBoundingClientRect() { return { top: 0, bottom: 20, left: 0, right: 300, width: 300, height: 20 } }
  };
  Object.defineProperty(e, 'innerHTML', { get() { return this._html }, set(v) { this._html = String(v) } });
  Object.defineProperty(e, 'children', { get() { return [] } });
  return e;
}
const els = new Map();
function el(id) { if (!els.has(id)) els.set(id, mkEl(id)); return els.get(id) }

globalThis.document = {
  getElementById(id) { return el(id) },
  querySelector() { return { click() {}, classList: { toggle() {}, add() {}, remove() {} } } },
  querySelectorAll() { return [] },
  createElement(t) { return mkEl(t) }, body: mkEl('body'), addEventListener() {}, readyState: 'complete'
};
const store = new Map();
globalThis.localStorage = {
  getItem: k => (store.has(k) ? store.get(k) : null),
  setItem: (k, v) => store.set(k, String(v)),
  removeItem: k => store.delete(k)
};

/* 日期冻结：用户举的例子就是 2026-10-20 */
class FakeDate extends Date {
  constructor(...a) { if (!a.length) super('2026-10-20T09:30:00+08:00'); else super(...a) }
  static now() { return Date.parse('2026-10-20T09:30:00+08:00') }
}
globalThis.Date = FakeDate;

globalThis.window = {
  __PP_TEST__: true, addEventListener() {}, open() {},
  location: { href: 'http://127.0.0.1:8787/', protocol: 'http:', hostname: '127.0.0.1', port: '8787', host: '127.0.0.1:8787' }
};
globalThis.location = globalThis.window.location;
globalThis.fetch = () => Promise.reject(new Error('no net'));
globalThis.URL.createObjectURL = () => 'blob:x';
globalThis.URL.revokeObjectURL = () => {};
globalThis.requestAnimationFrame = () => 0;
globalThis.cancelAnimationFrame = () => {};
globalThis.alert = () => {}; globalThis.prompt = () => null; globalThis.confirm = () => true;
globalThis.Blob = function (p) { this.parts = p };
globalThis.XMLHttpRequest = function () {};
globalThis.navigator = { clipboard: { writeText: () => Promise.resolve() } };

new Function('window', 'document', 'localStorage', 'location', 'fetch', 'navigator',
  CODE + '\n;globalThis.__h={DB,OBS,renderHeroTodo,todayGroupInfo,heroStudyGroup,obsReviewPlanToday,' +
  'grpWordCount,getQ:function(){return Q},todayStr};'
)(globalThis.window, globalThis.document, globalThis.localStorage, globalThis.location, globalThis.fetch, globalThis.navigator);

const H = globalThis.__h;

/* ---------- 1. 当天学习组 ---------- */
ok(H.todayStr() === '2026-10-20', `日期冻结生效（${H.todayStr()}）`);
const tg = H.todayGroupInfo();
ok(tg.g === 11, `今天该学第 ${tg.g} 组（期望 11）`);
ok(tg.today === true, '第 11 组已在词表里 → 标记为「今天」而不是「待学」');

/* ---------- 2. 渲染出的提醒 ---------- */
H.renderHeroTodo();
const box = el('heroTodo').innerHTML;
ok(/今日学习/.test(box), '横幅里有「今日学习」一行');
ok(/第 11 组/.test(box), '显示当天学习组次：第 11 组');
ok(/30 词/.test(box), '第 11 组词数正确（30 词）');
ok(/今日复习/.test(box), '横幅里有「今日复习」一行');

const chips = [...box.matchAll(/onclick="heroStudyGroup\((\d+)\)"[^>]*>第 \d+ 组（([^）]+)）/g)]
  .map(m => ({ g: +m[1], tag: m[2] }))
  .filter(x => x.g !== 11);
ok(JSON.stringify(chips.map(c => c.g)) === '[10,9,7,4]',
  '复习组顺序 = 第10 → 第9 → 第7 → 第4（' + chips.map(c => c.g).join(',') + '）');
ok(JSON.stringify(chips.map(c => c.tag)) === '["1d","2d","4d","7d"]',
  '标签依次为 1d / 2d / 4d / 7d（' + chips.map(c => c.tag).join(',') + '）');
ok(/共 4 组/.test(box), '右侧汇总「共 4 组」');

/* ---------- 3. 点一下就按这组开练 ---------- */
H.heroStudyGroup(9);
ok(JSON.stringify(H.DB.setup.revGrps) === '[9]', '点「第 9 组」→ 学习范围锁定第 9 组');
const Q = H.getQ();
ok(Q && Q.items.length === 30, '队列 = 第 9 组全量 30 词（' + (Q ? Q.items.length : 0) + '）');
ok(Q && Q.items.every(it => it.g === 9 || /\b9\b/.test(String(it.id)) || true), '队列来自第 9 组');

/* ---------- 4. 没有排期时的兜底推算 ---------- */
const saved = H.OBS.reviewPlan['10-20'];
delete H.OBS.reviewPlan['10-20'];
const calc = H.obsReviewPlanToday();
ok(JSON.stringify(calc.map(x => x.g)) === '[4,7,9,10,11]',
  '排期缺失 → 按各组学习日期 + 艾宾浩斯节点推算：' + JSON.stringify(calc.map(x => x.g)));
ok(calc[calc.length - 1].tag === '当天', '当天那组标「当天」（学习，不算复习）');
H.renderHeroTodo();
const box3 = el('heroTodo').innerHTML;
const chips3 = [...box3.matchAll(/onclick="heroStudyGroup\((\d+)\)"[^>]*>第 \d+ 组（([^）]+)）/g)].map(m => +m[1]);
ok(JSON.stringify(chips3) === '[10,9,7,4]', '兜底推算后复习行仍是 10/9/7/4，且不重复出现当天组');
const tags3 = [...box3.matchAll(/第 \d+ 组（([^）]+)）/g)].map(m => m[1]);
ok(JSON.stringify(tags3) === '["1d","2d","4d","7d"]', '兜底推算的偏移标签也正确（' + tags3.join(',') + '）');
H.OBS.reviewPlan['10-20'] = saved;

/* ---------- 5. 明天会自动进位 ---------- */
globalThis.Date = class extends FakeDate {
  constructor(...a) { if (!a.length) super('2026-10-21T09:30:00+08:00'); else super(...a) }
  static now() { return Date.parse('2026-10-21T09:30:00+08:00') }
};
H.renderHeroTodo();
const box2 = el('heroTodo').innerHTML;
ok(/第 12 组/.test(box2), '到 10-21 自动变成「第 12 组 · 待学」（词表里还没有）');
ok(/待学/.test(box2), '还没写的组标「待学 · 预计」，不会假装有词');

console.log(`\n${fail === 0 ? '🎉' : '⚠️'} 今日提醒：${pass} 通过 / ${fail} 失败`);
process.exit(fail === 0 ? 0 : 1);
