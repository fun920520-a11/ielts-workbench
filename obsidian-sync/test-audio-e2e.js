/* 端到端：页面 JS × 真实桥（8799）—— 状态 → 识别 → 中文匹配 → 落库
   前置：obsidian-sync 桥已在 8799 运行，且模型已就绪
   跑法：node test-audio-e2e.js */
const fs = require('fs');
const PAGE = 'C:/Users/24277/WorkBuddy/2026-10-17-16-23-57/index.html';
const WAV = 'C:/Users/24277/WorkBuddy/2026-10-17-16-23-57/podcast-bridge/podcasts/demo-voice.wav';
const BASE = process.env.BRIDGE || 'http://127.0.0.1:8799';
const html = fs.readFileSync(PAGE, 'utf8');
const CODE = [...html.matchAll(/<script(?![^>]*application\/json)[^>]*>([\s\S]*?)<\/script>/g)]
  .map(m => m[1]).join('\n');

let pass = 0, fail = 0;
const ok = (c, m) => { c ? (pass++, console.log('✅ ' + m)) : (fail++, console.log('❌ ' + m)) };

/* ---------- DOM 桩 ---------- */
function mkEl(id) {
  const e = {
    id, _html: '', textContent: '', value: '', style: {}, dataset: {}, className: '',
    classList: { _s: new Set(), add(c) { this._s.add(c) }, remove(c) { this._s.delete(c) },
      toggle(c, on) { on ? this._s.add(c) : this._s.delete(c) }, contains(c) { return this._s.has(c) } },
    appendChild(c) { return c }, removeChild() {}, remove() {},
    setAttribute(k, v) { this['__' + k] = v }, getAttribute(k) { return this['__' + k] ?? null },
    addEventListener() {}, removeEventListener() {}, focus() {}, click() {},
    querySelector() { return null }, querySelectorAll() { return [] },
    getBoundingClientRect() { return { top: 0, bottom: 20 } }, scrollIntoView() {}
  };
  Object.defineProperty(e, 'innerHTML', { get() { return this._html }, set(v) { this._html = String(v) } });
  return e;
}
const els = new Map();
const el = id => { if (!els.has(id)) els.set(id, mkEl(id)); return els.get(id) };
const audio = { id: 'au', src: '', currentTime: 0, duration: 0, paused: true,
  playbackRate: 1, play() { this.paused = false; return Promise.resolve() },
  pause() { this.paused = true }, load() {}, addEventListener() {} };
els.set('au', audio);
globalThis.document = {
  getElementById: id => (id === 'au' ? audio : el(id)),
  querySelector() { return null }, querySelectorAll() { return [] },
  createElement: t => mkEl(t), body: mkEl('body'), addEventListener() {}, readyState: 'complete'
};
const store = new Map();
globalThis.localStorage = { getItem: k => store.get(k) ?? null,
  setItem: (k, v) => store.set(k, String(v)), removeItem: k => store.delete(k) };
// 关键：把页面当成「本机直连版」，bridgeUrl() 返回 ''，请求走相对路径
globalThis.window = { __PP_TEST__: true, addEventListener() {},
  location: { protocol: 'http:', hostname: '127.0.0.1', port: '8799', host: '127.0.0.1:8799' } };
globalThis.location = globalThis.window.location;
globalThis.URL.createObjectURL = () => 'blob:x';
globalThis.URL.revokeObjectURL = () => {};
globalThis.requestAnimationFrame = () => 0;
globalThis.cancelAnimationFrame = () => {};
globalThis.alert = () => {};
globalThis.Blob = function (p) { this.parts = p };
globalThis.XMLHttpRequest = function () {};

const realFetch = globalThis.fetch;
globalThis.fetch = (url, opt) => realFetch(BASE + url, opt);

new Function('window', 'document', 'localStorage', 'location',
  CODE + '\n;globalThis.__au={AU,auBoot,auTranscribe,auRender,auReq,alignZh,auSave,auFindActive,' +
  'getST:function(){return AU_ST}};'
)(globalThis.window, globalThis.document, globalThis.localStorage, globalThis.location);
const A = globalThis.__au;

const sleep = ms => new Promise(r => setTimeout(r, ms));
async function waitFor(fn, ms, label) {
  const t0 = Date.now();
  while (Date.now() - t0 < ms) {
    try { if (await fn()) return true } catch (e) {}
    await sleep(400);
  }
  console.log('   ⏱ 超时：' + label);
  return false;
}

(async () => {
  /* 1. 桥状态 */
  A.auBoot();
  const stOk = await waitFor(() => A.getST() && A.getST().installed === true, 8000, 'ASR 状态');
  ok(stOk, '页面读到桥状态：ASR 已安装');
  ok(A.getST().modelCached === true, '模型已在本地（modelCached）');
  const tip = el('auBridgeTip');
  ok(/ASR 已就绪/.test(tip.innerHTML), '顶部提示显示「ASR 已就绪」');
  ok(!/没连上/.test(tip.innerHTML), '没有误报「没连上本机桥」');

  /* 2. 上传（页面用 XHR；这里用等价请求把 id 灌进去） */
  const buf = fs.readFileSync(WAV);
  const up = await realFetch(BASE + '/api/asr/upload?name=demo-voice.wav',
    { method: 'POST', headers: { 'Content-Type': 'application/octet-stream' }, body: buf })
    .then(r => r.json());
  ok(up.ok && up.id, '音频上传成功（id=' + up.id + '，时长 ' + up.dur + 's）');
  A.AU.id = up.id; A.AU.name = up.name; A.AU.dur = up.dur;
  audio.src = BASE + '/api/asr/audio?id=' + up.id;
  audio.duration = up.dur;

  /* 3. 页面发起识别（走 auReq → /api/asr/jobs → 轮询） */
  const t0 = Date.now();
  A.auTranscribe();
  const got = await waitFor(() => A.AU.cues.length > 0, 180000, '转写');
  ok(got, `英文字幕生成：${A.AU.cues.length} 句，用时 ${((Date.now() - t0) / 1000).toFixed(1)}s`);
  ok(A.AU.cues.length === 3, `句数正确（实为 ${A.AU.cues.length}）`);
  ok(A.AU.cues.every(c => c.et > c.st), '每句结束时间都大于开始时间');
  ok(A.AU.cues.every(c => /[A-Za-z]/.test(c.en)), '每句都有英文内容（无空句）');
  const mono = A.AU.cues.every((c, i) => i === 0 || c.st >= A.AU.cues[i - 1].st);
  ok(mono, '时间戳单调递增');
  ok(A.AU.cues[0].st < 0.5, `首句从 ${A.AU.cues[0].st}s 开始（贴近 0）`);
  ok(A.AU.cues[2].et <= up.dur + 0.05, `末句结束 ${A.AU.cues[2].et}s 未越过音频时长 ${up.dur}s`);

  /* 4. 中文按句匹配 + 落库 */
  el('auZh').value = '这座城市在过去十年里变化很大。\n我还记得街角那家小书店，店主以前会替我留一份早报。\n现在那里是家咖啡馆，租金涨了三倍。';
  const r = A.alignZh(A.AU.cues, el('auZh').value);
  ok(r.ok && /逐句对齐/.test(r.note), '中文 3 句 = 英文 3 句 → 逐句对齐');
  ok(A.AU.cues.every(c => !!c.zh), '三句都配上了中文');
  A.auRender();
  ok((el('auSubs').innerHTML.match(/au-cue/g) || []).length === 3, '界面渲染出 3 行双语字幕');
  ok(el('auSubs').innerHTML.includes('这座城市在过去十年里变化很大。'), '中文渲染进字幕行');

  await A.auReq('/api/asr/cues', { method: 'POST', body: {
    id: A.AU.id,
    cues: A.AU.cues.map(c => ({ st: c.st, et: c.et, en: c.en, zh: c.zh })),
    zhLines: el('auZh').value
  }});
  const saved = await realFetch(BASE + '/api/asr/cues?id=' + A.AU.id).then(r => r.json());
  ok((saved.cues || []).length === 3, '字幕已写入桥（重新打开也在）');
  ok(saved.cues.every(c => !!c.zh), '中文翻译一并持久化');
  ok(saved.zhLines && saved.zhLines.length > 10, '中文原文也存了（下次可回填输入框）');

  /* 5. 音频可拖动（Range） */
  const rg = await realFetch(BASE + '/api/asr/audio?id=' + A.AU.id,
    { headers: { Range: 'bytes=0-2047' } });
  ok(rg.status === 206, `音频支持 Range 拖动（HTTP ${rg.status}）`);
  ok(/\d+-\d+\/\d+/.test(rg.headers.get('content-range') || ''), 'Content-Range 正确：' + rg.headers.get('content-range'));

  /* 6. 页面上的点句跳播 */
  A.AU.cues[0] && (audio.currentTime = 0);
  const idx = A.auFindActive(A.AU.cues[1].st + 0.2);
  ok(idx === 1, '按时间点能否定位到第 2 句：' + idx);

  console.log(`\n${fail === 0 ? '🎉' : '⚠️'} 端到端（页面 × 真实桥）：${pass} 通过 / ${fail} 失败`);
  process.exit(fail === 0 ? 0 : 1);
})().catch(e => { console.error('💥 ' + e.stack); process.exit(1) });
