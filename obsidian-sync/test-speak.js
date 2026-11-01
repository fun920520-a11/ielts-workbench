/* v10 功能冒烟：新词量档位 + 口语模块渲染 + 评分算法 */
const fs = require('fs');

const PAGE = 'C:/Users/24277/WorkBuddy/2026-10-17-16-23-57/index.html';
const html = fs.readFileSync(PAGE, 'utf8');
const seedM = html.match(/<script[^>]*id="obs-seed"[^>]*>([\s\S]*?)<\/script>/);
const SEED = seedM ? seedM[1].trim() : '';
const blocks = [...html.matchAll(/<script(?![^>]*application\/json)[^>]*>([\s\S]*?)<\/script>/g)].map(m => m[1]);
const MAIN = blocks.sort((a, b) => b.length - a.length)[0];

function mkEl(id) {
  const el = {
    id, _html: '', textContent: id === 'obs-seed' ? SEED : '', value: '', type: '', accept: '', files: null,
    style: {}, dataset: {}, children: [], options: [], className: '',
    get innerHTML() { return this._html }, set innerHTML(v) { this._html = String(v) },
    classList: { add() {}, remove() {}, toggle() {}, contains() { return false } },
    appendChild(c) { this.children.push(c); return c }, removeChild() {}, remove() {},
    setAttribute() {}, getAttribute() { return null },
    addEventListener() {}, removeEventListener() {}, focus() {}, click() {}, reset() {},
    querySelector() { return null }, querySelectorAll() { return [] },
    insertAdjacentHTML() {}, scrollIntoView() {}
  };
  return el;
}
const els = new Map();
const document = {
  getElementById(id) { if (!els.has(id)) els.set(id, mkEl(id)); return els.get(id) },
  querySelector() { return null }, querySelectorAll() { return [] },
  createElement() { return mkEl('created') }, addEventListener() {},
  body: mkEl('body'), documentElement: mkEl('html'), head: mkEl('head')
};
const store = new Map();
const localStorage = {
  getItem: k => (store.has(k) ? store.get(k) : null),
  setItem: (k, v) => store.set(k, String(v)),
  removeItem: k => store.delete(k), clear: () => store.clear()
};
globalThis.window = { addEventListener() {}, removeEventListener() {}, scrollTo() {}, location: { href: 'https://x', hostname: 'www.workbuddy.cn', port: '', host: 'x', protocol: 'https:' } };
globalThis.document = document;
globalThis.localStorage = localStorage;
globalThis.location = globalThis.window.location;
globalThis.fetch = () => Promise.reject(new TypeError('Failed to fetch'));
globalThis.URL.createObjectURL = () => 'blob:x';
globalThis.alert = () => {}; globalThis.prompt = () => null; globalThis.confirm = () => true;
globalThis.navigator = { clipboard: { writeText: () => Promise.resolve() } };

const runner = new Function('window', 'document', 'localStorage', 'fetch', 'alert', 'prompt', 'confirm', 'navigator',
  MAIN + '\n;globalThis.__api=function(){return {DB:DB,navTo:navTo,openSetup:openSetup,saveSetup:saveSetup,renderSpeak:renderSpeak,spkScore:spkScore,renderSpkHist:renderSpkHist,getQ:()=>Q,spkRecAdd:spkRecAdd,renderSpkRecs:renderSpkRecs,spkRecRemove:spkRecRemove,recs:()=>SPK_RECS,obsWords:()=>OBS.words}};');
runner(globalThis.window, document, localStorage, globalThis.fetch, globalThis.alert, globalThis.prompt, globalThis.confirm, globalThis.navigator);
const A = globalThis.__api();
const DB = A.DB;
const assert = (c, m) => { if (!c) { console.error('❌ ' + m); process.exit(1); } console.log('✅ ' + m); };

// ---- 1. 新词量档位 30-150（select 选项在页面 HTML 里，直接查源码） ----
const selHtml = (html.match(/<select id="suDaily">[\s\S]*?<\/select>/) || [''])[0];
assert(selHtml.includes('value="30"') && selHtml.includes('value="150"') && !/\bvalue="20"|value="40"|value="80"/.test(selHtml),
  '档位选项 = 30/60/90/120/150 → ' + (selHtml.match(/value="\d+"/g) || []).join(','));

// 旧档 40 兜底
DB.setup = { level: 'all', daily: 40 };
A.openSetup();
const su = document.getElementById('suDaily');
assert(String(su.value) === '40', '旧档 40 自动补「旧档」选项且选中 → ' + su.value);
su.value = '90';
A.saveSetup();
assert(DB.setup.daily === 90 && Array.isArray(DB.setup.revGrps), '改为 90 后保存生效 → daily=' + DB.setup.daily + ', revGrps 保留');

// ---- 2. 口语模块渲染（无 SR → 警告条；行数与素材一致） ----
DB.setup = { level: 'all', daily: 90, revGrps: [] };
A.navTo('speak');
const warn = document.getElementById('spkSRWarn');
assert(warn._html.includes('不支持语音识别'), '无 SR 环境显示浏览器提示条');
const seed = JSON.parse(SEED);
const nQuotes = (seed.episodes[0].quotes || []).length;
const listHtml = document.getElementById('spkList')._html;
const nRows = (listHtml.match(/spk-res-/g) || []).length;
assert(nRows === nQuotes, '摘句模式渲染 ' + nRows + ' 行（与素材一致）');

// 切到逐句对话
const modeEl = document.getElementById('spkMode');
modeEl.value = 'pair';
A.renderSpeak();
const nPairs = (seed.episodes[0].pairs || []).length;
assert((document.getElementById('spkList')._html.match(/spk-res-/g) || []).length === nPairs,
  '对话模式渲染 ' + nPairs + ' 行');
modeEl.value = 'quote';

// ---- 3. 评分算法 ----
const target = 'We might like to believe that we are accepting and tolerant';
const expDur = Math.max(1200, spkNormLen(target));
function spkNormLen(t) { return t.split(/\s+/).length / 2.3 * 1000; }
let r = A.spkScore(target, 'we might like to believe that we are accepting and tolerant', expDur);
assert(r.acc === 100 && r.miss.length === 0 && r.score >= 95, '完美朗读 → acc=100 score=' + r.score);
r = A.spkScore(target, 'we might like to believe that we are accepting', expDur);
assert(r.acc < 100 && r.miss.includes('tolerant'), '漏读 tolerant → 被标红 → miss=' + JSON.stringify(r.miss));
r = A.spkScore(target, 'we might like to believe that we are accepting and tolerant', expDur * 3);
assert(r.flu < 50, '耗时 3 倍 → 流畅度低 → flu=' + r.flu);
r = A.spkScore(target, 'we may like to believe that we are accepting and tolerant', expDur);
assert(r.acc === 91 && r.miss.includes('might'), 'might 读成 may → 准确 91%（10/11），miss=might → acc=' + r.acc + ' miss=' + JSON.stringify(r.miss));
assert(r.score <= 100, '总分不超过 100 → ' + r.score);

// ---- 4. 记录与最佳分 ----
DB.speak = [
  { d: '2026-10-18', tid: 'ep01|quote|q0', score: 72, acc: 80, flu: 60, comp: 90, en: 'x' },
  { d: '2026-10-18', tid: 'ep01|quote|q0', score: 88, acc: 92, flu: 85, comp: 95, en: 'x' }
];
A.renderSpkHist();
assert(document.getElementById('spkHist')._html.includes('88 分'), '练习记录显示最新 88 分');


// ---- 5. 录音回放 ----
const blob=new Blob([new Uint8Array([1,2,3])],{type:'audio/webm'});
const rec=A.spkRecAdd(blob,{en:'We might like to believe',score:83});
A.renderSpkRecs();
const recHtml=document.getElementById('spkRecList')._html;
assert(!!rec&&A.recs().length===1,'录音入库 → 共 '+A.recs().length+' 条');
assert(recHtml.includes('回放')&&recHtml.includes('83 分')&&recHtml.includes('We might like'),'回放列表显示时间/分数/句子 + ▶️ 回放按钮');
A.spkRecRemove(rec.id);
assert(A.recs().length===0&&document.getElementById('spkRecList')._html.includes('还没有录音'),'删除录音后列表回到空态');

// ---- 6. 词表来源=每日词汇分册（数量从快照推导，不写死） ----
const ws=A.obsWords();const gs=[...new Set(ws.map(w=>w.grp))].sort((a,b)=>a-b);
const expW=(seed.words||[]).length, expG=new Set((seed.words||[]).map(w=>w.grp)).size;
assert(ws.length===expW&&gs.length===expG,'词表来自每日词汇分册 → '+ws.length+' 词 / '+gs.length+' 组（'+gs.join(',')+'）');

console.log('\n🎉 口语模块冒烟全过');
process.exit(0);
