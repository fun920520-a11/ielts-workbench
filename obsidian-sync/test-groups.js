/* 功能冒烟：复习分组选择 → 保存 → 学习流程按范围过滤 */
const fs = require('fs');

const PAGE = 'C:/Users/24277/WorkBuddy/2026-10-17-16-23-57/index.html';
const html = fs.readFileSync(PAGE, 'utf8');

const seedM = html.match(/<script[^>]*id="obs-seed"[^>]*>([\s\S]*?)<\/script>/);
const SEED = seedM ? seedM[1].trim() : '';
const blocks = [...html.matchAll(/<script(?![^>]*application\/json)[^>]*>([\s\S]*?)<\/script>/g)].map(m => m[1]);
const MAIN = blocks.sort((a, b) => b.length - a.length)[0];

// ---------- DOM 桩（带 innerHTML 记忆 + 简易 querySelectorAll） ----------
function mkEl(id) {
  const el = {
    id, _html: '', textContent: id === 'obs-seed' ? SEED : '', value: '', type: '', accept: '', files: null,
    style: {}, dataset: {}, children: [], options: [],
    className: '',
    get innerHTML() { return this._html },
    set innerHTML(v) { this._html = String(v) },
    classList: { add() {}, remove() {}, toggle() {}, contains() { return false } },
    appendChild(c) { this.children.push(c); return c },
    removeChild() {}, remove() {}, setAttribute() {}, getAttribute() { return null },
    addEventListener() {}, removeEventListener() {}, focus() {}, click() {}, reset() {},
    querySelector() { return null }, querySelectorAll() { return [] },
    insertAdjacentHTML() {}, scrollIntoView() {}
  };
  return el;
}
const els = new Map();

function parseChips(html) {
  const out = [];
  const re = /<span class="chip( on)?" data-g="(\d+)"/g;
  let m;
  while ((m = re.exec(html))) {
    const g = +m[2], on = !!m[1];
    out.push({ g, on, getAttribute: () => String(g) });
  }
  return out;
}
const document = {
  getElementById(id) { if (!els.has(id)) els.set(id, mkEl(id)); return els.get(id) },
  querySelector() { return null },
  querySelectorAll(sel) {
    if (/suGrp(Chips|Extra)/.test(sel)) {
      let chips = [];
      ['suGrpChips', 'suGrpExtra'].forEach(id => {
        const el = els.get(id);
        if (el && el._html) chips = chips.concat(parseChips(el._html));
      });
      return sel.includes('.chip.on') ? chips.filter(c => c.on) : chips;
    }
    return [];
  },
  createElement() { return mkEl('created') },
  addEventListener() {},
  body: mkEl('body'),
  documentElement: mkEl('html'),
  head: mkEl('head')
};

const store = new Map();
const localStorage = {
  getItem: k => (store.has(k) ? store.get(k) : null),
  setItem: (k, v) => store.set(k, String(v)),
  removeItem: k => store.delete(k), clear: () => store.clear()
};

// 冻结日期到 2026-10-17，稳定复现用户举例的排期
class FakeDate extends Date {
  constructor(...args) { if (args.length === 0) super('2026-10-17T23:30:00+08:00'); else super(...args); }
  static now() { return Date.parse('2026-10-17T23:30:00+08:00'); }
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
  MAIN + '\n;globalThis.__api=function(){return {DB:DB,planToday:obsReviewPlanToday,revGrpSel:revGrpSel,startStudy:startStudy,openSetup:openSetup,saveSetup:saveSetup,getQ:()=>Q,obsWords:()=>OBS.words,grpOf:grpOf}};');
runner(globalThis.window, document, localStorage, globalThis.fetch, globalThis.alert, globalThis.prompt, globalThis.confirm, globalThis.navigator);

const A = globalThis.__api();
const DB = A.DB;
const assert = (cond, msg) => { if (!cond) { console.error('❌ ' + msg); process.exit(1); } console.log('✅ ' + msg); };

// ---- 1. 当日排期解析 ----
const plan = A.planToday();
assert(JSON.stringify(plan) === JSON.stringify([{ g: 1, tag: '7d' }, { g: 4, tag: '4d' }, { g: 6, tag: '2d' }, { g: 7, tag: '1d' }]),
  '当日排期 = 第1组(7d)/第4组(4d)/第6组(2d)/第7组(1d) → ' + JSON.stringify(plan));

// ---- 2. 弹窗 chips：默认全选当日 ----
DB.setup = { level: 'all', daily: 40, revGrps: [] };
A.openSetup();
const chips = parseChips(document.getElementById('suGrpChips').innerHTML);
assert(chips.length === 4 && chips.every(c => c.on) && JSON.stringify(chips.map(c => c.g)) === '[1,4,6,7]',
  '弹窗渲染 4 个当日分组 chip 且默认全选 → ' + JSON.stringify(chips.map(c => c.g)));

// ---- 3. 取消第 6 组 → saveSetup → DB.setup.revGrps=[1,4,7] ----
const fakeSel = chips.filter(c => c.g !== 6).map(c => ({ getAttribute: () => String(c.g) }));
const realQSA = document.querySelectorAll;
document.querySelectorAll = sel => (/suGrp(Chips|Extra)/.test(sel) && sel.includes('.chip.on')) ? fakeSel : realQSA(sel);
A.saveSetup();
document.querySelectorAll = realQSA;
assert(JSON.stringify(DB.setup.revGrps) === '[1,4,7]', '保存后 DB.setup.revGrps = ' + JSON.stringify(DB.setup.revGrps));

// ---- 4. 学习流程：复习词只来自选中组 ----
DB.wlog = {}; DB.wstat = {}; DB.zhan = {}; DB.daily = {};
const byGrp = {};
A.obsWords().forEach(w => { (byGrp[w.grp] = byGrp[w.grp] || []).push(w.id) });
[1, 4, 6, 7].forEach(g => {
  (byGrp[g] || []).slice(0, 3).forEach(id => { DB.wlog[id + '|2026-10-10'] = 'done'; });  // gap=7 → 到期
});
A.startStudy();
let Q = A.getQ();
assert(Q && Q.active, 'startStudy() 启动学习队列');
const rev = Q.items.filter(it => it.isRev);
const revGrps = [...new Set(rev.map(it => A.grpOf(it.id)))].sort();
assert(rev.length >= 9 && !revGrps.includes(6) && JSON.stringify(revGrps) === '[1,4,7]',
  '复习词 ' + rev.length + ' 个，组别 ' + JSON.stringify(revGrps) + '（第 6 组被排除）');

// ---- 5. 清空范围 → 恢复复习全部 ----
DB.setup.revGrps = [];
A.startStudy();
Q = A.getQ();
const rev2 = Q.items.filter(it => it.isRev);
const rev2Grps = [...new Set(rev2.map(it => A.grpOf(it.id)))].sort();
assert(rev2Grps.includes(6), '不限分组时第 6 组复习词回归 → 组别 ' + JSON.stringify(rev2Grps));

console.log('\n🎉 复习分组全链路通过');
process.exit(0);
