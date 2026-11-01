/* v12 冒烟：学习范围硬边界（选组=只出这些组、且整组全量）+ 每词标组次 */
const fs = require('fs');

const PAGE = 'C:/Users/24277/WorkBuddy/2026-10-17-16-23-57/index.html';
const html = fs.readFileSync(PAGE, 'utf8');

const seedM = html.match(/<script[^>]*id="obs-seed"[^>]*>([\s\S]*?)<\/script>/);
const SEED = seedM ? seedM[1].trim() : '';
const blocks = [...html.matchAll(/<script(?![^>]*application\/json)[^>]*>([\s\S]*?)<\/script>/g)].map(m => m[1]);
const MAIN = blocks.sort((a, b) => b.length - a.length)[0];

function mkEl(id) {
  return {
    id, _html: '', textContent: id === 'obs-seed' ? SEED : '', value: '', type: '', accept: '', files: null,
    style: {}, dataset: {}, children: [], options: [], className: '',
    get innerHTML() { return this._html },
    set innerHTML(v) { this._html = String(v) },
    classList: { add() {}, remove() {}, toggle() {}, contains() { return false } },
    appendChild(c) { this.children.push(c); return c },
    removeChild() {}, remove() {}, setAttribute() {}, getAttribute() { return null },
    addEventListener() {}, removeEventListener() {}, focus() {}, click() {}, reset() {},
    querySelector() { return null }, querySelectorAll() { return [] },
    insertAdjacentHTML() {}, scrollIntoView() {}
  };
}
const els = new Map();
const document = {
  getElementById(id) { if (!els.has(id)) els.set(id, mkEl(id)); return els.get(id) },
  querySelector() { return null },
  querySelectorAll() { return [] },
  createElement() { return mkEl('created') },
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
  constructor(...args) { if (args.length === 0) super('2026-10-19T20:10:00+08:00'); else super(...args); }
  static now() { return Date.parse('2026-10-19T20:10:00+08:00'); }
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
    DB:DB, startStudy:startStudy, getQ:()=>Q, obsWords:()=>OBS.words, grpOf:grpOf,
    inScope:inScope, distract:distract, renderWList:renderWList, renderQ:renderQ,
    scopeWordCount:scopeWordCount, counts:()=>OBS.counts
  }};`);
runner(globalThis.window, document, localStorage, globalThis.fetch, globalThis.alert, globalThis.prompt, globalThis.confirm, globalThis.navigator);

const A = globalThis.__api();
const DB = A.DB;
const assert = (cond, msg) => { if (!cond) { console.error('❌ ' + msg); process.exit(1); } console.log('✅ ' + msg); };
const byGrp = {};
A.obsWords().forEach(w => { (byGrp[w.grp] = byGrp[w.grp] || []).push(w); });

// ---- 1. 词表完整性：第 10 组必须在 ----
/* 期望值从内嵌快照推导，词表每天在长，不写死 */
const SEED_OBJ = JSON.parse(SEED);
const expWords = (SEED_OBJ.words || []).length;
const expGrps = new Set((SEED_OBJ.words || []).map(w => w.grp)).size;
assert(A.obsWords().length === expWords, '词表共 ' + A.obsWords().length + ' 词（= 快照 ' + expWords + '）');
assert(Object.keys(byGrp).length === expGrps, '分组数 ' + Object.keys(byGrp).length + '（= 快照 ' + expGrps + '）');
assert((byGrp[10] || []).length === 30, '第 10 组解析到 ' + (byGrp[10] || []).length + ' 词（应为 30）');
assert((byGrp[10] || []).some(w => w.w === 'crime'), '第 10 组包含 crime');

// ---- 2. 选第 9 组 → 队列只出第 9 组，且整组全量 ----
DB.setup = { level: 'all', daily: 60, revGrps: [9] };
DB.wlog = {}; DB.wstat = {}; DB.zhan = {}; DB.daily = {};
A.startStudy();
let Q = A.getQ();
assert(Q && Q.active, 'startStudy() 启动学习队列');
let gs = [...new Set(Q.items.map(it => A.grpOf(it.id)))].sort((a, b) => a - b);
assert(JSON.stringify(gs) === '[9]', '队列组别只有第 9 组 → ' + JSON.stringify(gs));
assert(Q.items.length === 30, '第 9 组整组全量入队 ' + Q.items.length + ' 词（应为 30，不受每日 60 上限截断）');
const ids9 = new Set(byGrp[9].map(w => w.id));
assert(Q.items.every(it => ids9.has(it.id)), '队列中每个词都属于第 9 组（无夹杂）');
assert(new Set(Q.items.map(it => it.id)).size === 30, '30 个词互不重复');

// ---- 3. 多选 9+10 → 60 词，两组 ----
DB.setup.revGrps = [9, 10];
A.startStudy();
Q = A.getQ();
gs = [...new Set(Q.items.map(it => A.grpOf(it.id)))].sort((a, b) => a - b);
assert(JSON.stringify(gs) === '[9,10]' && Q.items.length === 60,
  '多选 9+10 → ' + Q.items.length + ' 词 / 组别 ' + JSON.stringify(gs));

// ---- 4. 干扰项不得越界 ----
DB.setup.revGrps = [9];
const target = byGrp[9][0];
const ds = A.distract([target.w, target.ipa, target.zh, '*', target.id], 2, 3);
const dsGrp = ds.map(x => x[4]).map(id => { const m = A.obsWords().find(w => w.id === id); return m ? m.grp : null });
assert(dsGrp.length === 3 && dsGrp.every(g => g === 9), '选项干扰词全部来自第 9 组 → ' + JSON.stringify(dsGrp));

// ---- 5. 单词本每行带组次 ----
DB.setup.revGrps = [];
A.renderWList();
const wl = document.getElementById('wList').innerHTML;
assert(/<span class="w maskable">crime<\/span><span class="gtag"[^>]*>第 10 组<\/span>/.test(wl), '单词本 crime 行显示「第 10 组」');
assert((wl.match(/class="gtag"/g) || []).length >= expWords, '单词本 ' + (wl.match(/class="gtag"/g) || []).length + ' 行都带组次徽标');

// ---- 6. 学习卡片也带组次 ----
DB.setup.revGrps = [9];
A.startStudy();
A.renderQ();
const qa = document.getElementById('quizArea').innerHTML;
assert(/第 9 组/.test(qa), '答题卡头部显示「第 9 组」');
assert(/class="pill"/.test(qa) && /第 9 组/.test(qa), '题目区域带组次徽标');

console.log('\n🎉 v12 学习范围与组次标注全链路通过');
process.exit(0);
