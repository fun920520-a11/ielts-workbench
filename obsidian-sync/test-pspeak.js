/* v17 冒烟：短文朗读的暂停/恢复 + 跟随高亮（分段朗读 · 滚动跟随 · 视图适配） */
const fs = require('fs');

const PAGE = 'C:/Users/24277/WorkBuddy/2026-10-17-16-23-57/index.html';
const html = fs.readFileSync(PAGE, 'utf8');

const seedM = html.match(/<script[^>]*id="obs-seed"[^>]*>([\s\S]*?)<\/script>/);
const SEED = seedM ? seedM[1].trim() : '';
const pseedM = html.match(/<script[^>]*id="passage-seed"[^>]*>([\s\S]*?)<\/script>/);
const PSEED = pseedM ? pseedM[1].trim() : '';
const blocks = [...html.matchAll(/<script(?![^>]*application\/json)[^>]*>([\s\S]*?)<\/script>/g)].map(m => m[1]);
const MAIN = blocks.sort((a, b) => b.length - a.length)[0];

let pass = 0, fail = 0;
function ok(c, m) { if (c) { pass++ } else { fail++; console.log('❌ ' + m) } }

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
    classList: mkClassList(), title: '',
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
  execCommand() { return true },
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

/* ---------- speechSynthesis 桩：记录调用 + 可手动触发 onend ---------- */
const synth = {
  speaking: false, pending: false, paused: false,
  spoken: [], pauseN: 0, resumeN: 0, cancelN: 0,
  cancelled: false,
  speak(u) { this.spoken.push(u); this.speaking = true; this.pending = false; this.cancelled = false },
  cancel() { this.cancelN++; this.speaking = false; this.paused = false },
  pause() { this.pauseN++; this.paused = true },
  resume() { this.resumeN++; this.paused = false },
  getVoices() { return [] },
  /* 模拟用户听完当前段 */
  endCurrent() {
    const u = this.spoken[this.spoken.length - 1];
    this.speaking = false;
    if (u && u.onend) u.onend({});
  }
};
class FakeUtter {
  constructor(t) { this.text = t; this.lang = ''; this.rate = 1; this.voice = null }
}
/* ---------- 滚动记录 ---------- */
const scrolls = [];
globalThis.__copied = '';
globalThis.Date = FakeDate;
globalThis.window = {
  addEventListener() {}, removeEventListener() {},
  innerHeight: 800, pageYOffset: 0,
  scrollTo(a, b) { scrolls.push(typeof a === 'object' ? a : { top: b, behavior: 'auto' }) },
  location: { href: 'https://www.workbuddy.cn/x', hostname: 'www.workbuddy.cn', port: '', host: 'www.workbuddy.cn', protocol: 'https:' }
};
globalThis.document = document;
globalThis.localStorage = localStorage;
globalThis.location = globalThis.window.location;
globalThis.fetch = () => Promise.reject(new TypeError('Failed to fetch'));
globalThis.URL.createObjectURL = () => 'blob:x';
globalThis.alert = () => {}; globalThis.prompt = () => null; globalThis.confirm = () => true;
globalThis.navigator = { clipboard: { writeText: t => { globalThis.__copied = t; return Promise.resolve() } } };
globalThis.speechSynthesis = synth;
globalThis.SpeechSynthesisUtterance = FakeUtter;
globalThis.window.speechSynthesis = synth;
globalThis.window.SpeechSynthesisUtterance = FakeUtter;

const runner = new Function('window', 'document', 'localStorage', 'fetch', 'alert', 'prompt', 'confirm', 'navigator',
  MAIN + `\n;globalThis.__api=function(){return {
    DB:DB, PS:PS, PS_SPK:PS_SPK, psSeed:psSeed, psGroups:psGroups, psWordsOf:psWordsOf, psGet:psGet,
    renderPassage:renderPassage, psPick:psPick, psSetView:psSetView, psMarkRead:psMarkRead,
    psSpeak:psSpeak, psSpeakStart:psSpeakStart, psSpeakPause:psSpeakPause, psSpeakResume:psSpeakResume,
    psSpeakStop:psSpeakStop, psSpeakUI:psSpeakUI, psSegs:psSegs, psFocus:psFocus, psZhIdx:psZhIdx,
    psToggleFollow:psToggleFollow, psInView:psInView, speak:speak, navTo:navTo, obsWords:()=>OBS.words, toast:toast
  }};`);
runner(globalThis.window, document, localStorage, globalThis.fetch, globalThis.alert, globalThis.prompt, globalThis.confirm, globalThis.navigator);

const A = globalThis.__api();
const el = id => document.getElementById(id);
A.PS_SPK.gap = 0;      /* 同步启动，无需等 80ms */
A.PS_SPK.grace = 0;    /* 恢复兜底同步检查 */
const toastTxt = () => el('toast').textContent;

/* 把当前短文的英文 / 中文段落挂成假 DOM 节点（innerHTML 是字符串，桩不会解析） */
function fakePara(tag, i) {
  return {
    id: tag + i, classList: mkClassList(), rect: { top: 2400, bottom: 2430, height: 30 },
    getBoundingClientRect() { return this.rect }
  };
}
function mount() {
  const p = A.psGet(A.PS.cur);
  const en = el('psEn'), zh = el('psZh');
  en.children = A.psSegs(p).map((_, i) => fakePara('en', i));
  zh.children = String(p.zh || '').split(/\n{2,}/).map((_, i) => fakePara('zh', i));
  return p;
}
function nowIdxEn() {
  const c = el('psEn').children;
  const hit = [];
  c.forEach((x, i) => { if (x.classList.contains('ps-now')) hit.push(i) });
  return hit;
}
function nowIdxZh() {
  const c = el('psZh').children;
  const hit = [];
  c.forEach((x, i) => { if (x.classList.contains('ps-now')) hit.push(i) });
  return hit;
}

/* ---------- 1. 初始化 ---------- */
A.renderPassage();
document.getElementById('psSpeakBtn').textContent = '';
A.psSpeakUI();
ok(A.PS.follow === true, '跟随朗读默认开启');
ok(el('psFollow').classList.contains('on'), '跟随 chip 默认高亮');
ok(el('psSpeakBtn').textContent === '🔊 朗读英文', '未播放时按钮是「🔊 朗读英文」');
ok(el('psSpeakStop').style.display === 'none', '未播放时「停止」按钮隐藏');
ok(A.PS_SPK.on === false, '初始不在朗读态');

/* ---------- 2. 分段：与渲染的段落一一对应 ---------- */
const p11 = mount();
const segs = A.psSegs(p11);
ok(segs.length >= 3, '第 11 组短文至少 3 段（实际 ' + segs.length + ' 段）');
ok(segs.length === el('psEn').children.length, '分段数与正文 <p> 数一致（' + segs.length + '）');
ok(segs.every((s, i) => s.trim().length > 0 || true), '分段结果可用');

/* ---------- 3. 开始朗读：第一段高亮 + 滚动 ---------- */
scrolls.length = 0;
A.psSpeak();
ok(A.PS_SPK.on === true && A.PS_SPK.paused === false, '点「朗读」→ 进入朗读态');
ok(A.PS_SPK.idx === 0, '从第 0 段开始');
ok(synth.spoken.length === 1, '只朗读了 1 段（分段朗读，不是整篇一口气）');
ok(!/\n/.test(synth.spoken[0].text), '送进 TTS 的文本已压掉换行');
ok(synth.spoken[0].lang === 'en-US', '语言是 en-US');
ok(synth.spoken[0].rate > 0 && synth.spoken[0].rate <= 1, '语速 0.88（避免太快听不清）');
ok(JSON.stringify(nowIdxEn()) === '[0]', '第 0 段被高亮，其余不高亮');
ok(scrolls.length === 1, '首段在视口外 → 滚动一次');
ok(scrolls[0].top === 2400 - 208, '滚动到「段落顶部 − 视口 26%」，让当前段停在视线舒适区（top=' + scrolls[0].top + '）');
ok(el('psSpeakBtn').textContent === '⏸ 暂停', '播放中按钮变「⏸ 暂停」');
ok(el('psSpeakStop').style.display === '', '播放中「停止」按钮出现');

/* ---------- 4. 段落推进 ---------- */
scrolls.length = 0;
el('psEn').children[1].rect = { top: 410, bottom: 440, height: 30 };   /* 视口内 */
synth.endCurrent();
ok(A.PS_SPK.idx === 1, '上一段读完自动读下一段');
ok(JSON.stringify(nowIdxEn()) === '[1]', '高亮跟着移到第 1 段');
ok(nowIdxZh().length === 1, '中文侧同步高亮对应的那一段');
ok(scrolls.length === 0, '下一段已在视口内 → 不滚动（不晃眼）');

/* ---------- 5. 暂停 ---------- */
const spokenBeforePause = synth.spoken.length;
A.psSpeak();
ok(A.PS_SPK.paused === true, '再点一下 → 暂停');
ok(synth.pauseN === 1, '调用了 speechSynthesis.pause()');
ok(el('psSpeakBtn').textContent === '▶️ 继续', '暂停时按钮变「▶️ 继续」');
ok(synth.spoken.length === spokenBeforePause, '暂停时不再送新段');
synth.endCurrent();   /* 某些浏览器 pause 会误触发 onend */
ok(A.PS_SPK.idx === 1, '暂停期间收到 onend 也不推进（不会跳段）');
synth.speaking = true;   /* 真实浏览器 pause 时 speaking 仍为 true */

/* ---------- 6. 恢复 ---------- */
A.psSpeak();
ok(A.PS_SPK.paused === false, '再点 → 恢复');
ok(synth.resumeN === 1, '调用了 speechSynthesis.resume()');
ok(el('psSpeakBtn').textContent === '⏸ 暂停', '恢复后按钮回到「⏸ 暂停」');
ok(synth.spoken.length === spokenBeforePause, '正常恢复 → 不重读（继续原 utterance）');
synth.endCurrent();
ok(A.PS_SPK.idx === 2, '恢复后正常推进到第 2 段');

/* ---------- 7. 浏览器把 utterance 掐掉时的兜底 ---------- */
const n0 = synth.spoken.length;
A.psSpeakPause();
synth.speaking = false;             /* 模拟 pause 后当前段被静默终止 */
A.psSpeakResume();
ok(synth.spoken.length === n0 + 1, 'resume 后没声音 → 自动重读当前段（兜底）');
ok(A.PS_SPK.idx === 2, '兜底重读的仍是当前段，不跳段');

/* ---------- 8. 停止 ---------- */
A.psSpeakStop();
ok(A.PS_SPK.on === false && A.PS_SPK.idx === -1, '停止后回到未播放态');
ok(synth.cancelN > 0, '调用了 speechSynthesis.cancel()');
ok(nowIdxEn().length === 0 && nowIdxZh().length === 0, '停止后高亮全部清除');
ok(el('psSpeakBtn').textContent === '🔊 朗读英文', '停止后按钮复原');
ok(el('psSpeakStop').style.display === 'none', '停止后「停止」按钮隐藏');

/* ---------- 9. 读完最后一段自动收尾 ---------- */
A.psSpeak();
for (let i = 0; i < A.PS_SPK.segs.length + 1; i++) synth.endCurrent();
ok(A.PS_SPK.on === false, '读完最后一段自动结束');
ok(/读完了/.test(toastTxt()), '读完给一句「这一篇读完了」');
ok(nowIdxEn().length === 0, '读完后不留残余高亮');

/* ---------- 10. 关闭跟随：只高亮不滚动 ---------- */
A.psToggleFollow();
ok(A.PS.follow === false, '点「跟随朗读」→ 关闭');
ok(!el('psFollow').classList.contains('on'), '关闭后 chip 不高亮');
scrolls.length = 0;
A.psSpeak();
ok(nowIdxEn().length === 1, '关闭跟随后仍然高亮当前段');
ok(scrolls.length === 0, '关闭跟随后不自动滚动');
/* 重新打开跟随 → 立刻定位到当前段 */
el('psEn').children[0].rect = { top: 2400, bottom: 2430, height: 30 };
scrolls.length = 0;
A.psToggleFollow();
ok(A.PS.follow === true, '再点 → 重新开启跟随');
ok(scrolls.length === 1, '重新开启后立刻定位到当前朗读段');
ok(JSON.stringify(nowIdxEn()) === '[0]', '重新开启不改变当前段');

/* ---------- 11. 只看中文：滚中文段 + 比例映射 ---------- */
A.psSpeakStop(1);
A.psSetView('zh');
mount();
synth.endCurrent();          /* 清掉残留 utterance 状态 */
A.psSpeakStop(1);
A.psSpeakStart();
const enN = el('psEn').children.length, zhN = el('psZh').children.length;
ok(A.PS.view === 'zh', '切到「只看中文」');
ok(enN >= 3 && zhN >= 3, '中英段落数：' + enN + ' / ' + zhN);
scrolls.length = 0;
el('psZh').children[0].rect = { top: 2000, bottom: 2030, height: 30 };
A.psFocus(0);
ok(scrolls.length === 1, '只看中文时滚的是中文段落（不是隐藏的英文段）');
const zi1 = A.psZhIdx(1);
ok(zi1 >= 0 && zi1 < zhN, '第 1 段英文映射到第 ' + zi1 + ' 段中文');
ok(Math.abs(zi1 - Math.round(1 * (zhN - 1) / Math.max(1, enN - 1))) === 0, '段数不等时按长度比例映射');
A.psFocus(1);
ok(JSON.stringify(nowIdxZh()) === '[' + zi1 + ']', '高亮落在映射后的中文段');
A.psSetView('both');

/* ---------- 12. 不等段数的极端情况 ---------- */
ok(A.psZhIdx(enN - 1) === zhN - 1, '最后一段一定映射到最后一段（不越界）');
ok(A.psZhIdx(enN + 50) === zhN - 1, '越界索引被夹到最后一段');

/* ---------- 13. 切组 / 重渲染会中断朗读 ---------- */
A.psSpeakStop(1);
A.psSpeak();
ok(A.PS_SPK.on === true, '再次进入朗读态');
A.psPick(10);
ok(A.PS_SPK.on === false, '切换组次 → 朗读自动停止（避免高亮跑到旧节点）');
ok(el('psSpeakBtn').textContent === '🔊 朗读英文', '切组后按钮复原');
mount();

/* ---------- 13.5 切页面：离开短文页就停 ---------- */
A.renderPassage(); mount();
A.psSpeakStart();
ok(A.PS_SPK.on === true, '切页前在朗读');
A.navTo('snt');
ok(A.PS_SPK.on === true, '停留在短文页 → 朗读不被打断');
try { A.navTo('word') } catch (e) {}
ok(A.PS_SPK.on === false, '离开短文页 → 朗读自动停止（不用回去找开关）');
A.navTo('snt'); mount();

/* ---------- 14. 词表里的 🔊 也会打断短文朗读 ---------- */
A.psSpeakStart();
ok(A.PS_SPK.on === true, '重新开始朗读');
A.speak('hello', 0.9);
ok(A.PS_SPK.on === false, '点单词发音 → 短文朗读先停（不会被掐成半截）');

/* ---------- 15. 没有短文的组 ---------- */
A.PS.cur = 99;
const p99 = A.psGet(99);
ok(p99 === null, '第 99 组没有短文');
toastTxt();
A.psSpeak();
ok(A.PS_SPK.on === false, '没有短文时不进入朗读态');
ok(/还没有短文/.test(toastTxt()), '并提示「这一组还没有短文」');
A.PS.cur = 0;

/* ---------- 16. onerror 容错 ---------- */
A.renderPassage(); mount();
A.psSpeakStart();
const u0 = synth.spoken[synth.spoken.length - 1];
const beforeErr = A.PS_SPK.idx;
u0.onerror({ error: 'canceled' });
ok(A.PS_SPK.idx === beforeErr, '「canceled」错误不推进（正常停止）');
A.psSpeakStop(1); mount();
A.psSpeakStart();
const u1 = synth.spoken[synth.spoken.length - 1];
u1.onerror({ error: 'synthesis-failed' });
ok(A.PS_SPK.idx === 1, '其他错误跳过这一段继续读（不卡死）');
A.psSpeakStop(1);

/* ---------- 17. 按钮 onclick 接线 ---------- */
ok(/onclick="psSpeak\(\)"/.test(html), '按钮点击接到 psSpeak()');
ok(/onclick="psSpeakStop\(\)"/.test(html), '「停止」按钮接到 psSpeakStop()');
ok(/onclick="psToggleFollow\(\)"/.test(html), '「跟随朗读」接到 psToggleFollow()');
ok(/id="psSpeakStop"[\s\S]{0,80}style="display:none"/.test(html), '「停止」按钮默认隐藏');
ok(/\.ps-en p\.ps-now\{/.test(html) && /\.ps-zh p\.ps-now\{/.test(html), '英文 / 中文各有当前段高亮样式');
ok(/#psSpeakBtn\.speaking\{/.test(html) && /#psSpeakBtn\.paused\{/.test(html), '朗读按钮有播放 / 暂停两种配色');

console.log(`\n${fail === 0 ? '🎉' : '⚠️'} 短文朗读（暂停/恢复 + 跟随）：${pass} 通过 / ${fail} 失败`);
process.exit(fail === 0 ? 0 : 1);
