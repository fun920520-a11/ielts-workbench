/* 本地音频精听模块回归：中文按句匹配 / 时间轴 / 点句跳播 / SRT
   跑法：node test-audio.js */
const fs = require('fs');
const PAGE = 'C:/Users/24277/WorkBuddy/2026-10-17-16-23-57/index.html';
const html = fs.readFileSync(PAGE, 'utf8');
const CODE = [...html.matchAll(/<script(?![^>]*application\/json)[^>]*>([\s\S]*?)<\/script>/g)]
  .map(m => m[1]).join('\n');

let pass = 0, fail = 0;
function ok(c, msg) {
  if (c) { pass++; console.log('✅ ' + msg) } else { fail++; console.log('❌ ' + msg) }
}

/* ---------- DOM 桩 ---------- */
function mkEl(id) {
  const e = {
    id, _html: '', textContent: '', value: '', style: {}, dataset: {}, className: '',
    classList: {
      _s: new Set(),
      add(c) { this._s.add(c) }, remove(c) { this._s.delete(c) },
      toggle(c, on) { on === undefined ? (this._s.has(c) ? this._s.delete(c) : this._s.add(c)) : (on ? this._s.add(c) : this._s.delete(c)) },
      contains(c) { return this._s.has(c) }
    },
    appendChild(c) { return c }, removeChild() {}, remove() {},
    setAttribute(k, v) { this['__' + k] = v }, getAttribute(k) { return this['__' + k] ?? null },
    addEventListener() {}, removeEventListener() {}, focus() {}, click() {},
    querySelector() { return null }, querySelectorAll() { return [] },
    getBoundingClientRect() { return { top: 0, bottom: 20, left: 0, right: 300, width: 300, height: 20 } },
    scrollIntoView() {}
  };
  Object.defineProperty(e, 'innerHTML', {
    get() { return this._html }, set(v) { this._html = String(v) }
  });
  Object.defineProperty(e, 'children', { get() { return [] } });
  return e;
}
const els = new Map();
function el(id) { if (!els.has(id)) els.set(id, mkEl(id)); return els.get(id) }

// 假音频元素
const audio = {
  id: 'au', src: '', currentTime: 0, duration: 18, paused: true, playbackRate: 1,
  played: 0,
  play() { this.paused = false; this.played++; return Promise.resolve() },
  pause() { this.paused = true },
  load() {}, addEventListener() {}
};
els.set('au', audio);

globalThis.document = {
  getElementById(id) {
    if (id === 'au') return audio;
    return el(id);
  },
  querySelector() { return null }, querySelectorAll() { return [] },
  createElement(t) { return mkEl(t) }, body: mkEl('body'),
  addEventListener() {}, readyState: 'complete'
};
const store = new Map();
globalThis.localStorage = {
  getItem: k => (store.has(k) ? store.get(k) : null),
  setItem: (k, v) => store.set(k, String(v)),
  removeItem: k => store.delete(k)
};
globalThis.window = {
  __PP_TEST__: true, addEventListener() {},
  location: { protocol: 'http:', hostname: '127.0.0.1', port: '8787', host: '127.0.0.1:8787' }
};
globalThis.location = globalThis.window.location;
globalThis.fetch = () => Promise.reject(new Error('no net'));
globalThis.URL.createObjectURL = () => 'blob:x';
globalThis.URL.revokeObjectURL = () => {};
globalThis.requestAnimationFrame = () => 0;
globalThis.cancelAnimationFrame = () => {};
globalThis.alert = () => {};
globalThis.Blob = function (parts) { this.parts = parts };
globalThis.XMLHttpRequest = function () {};

new Function('window', 'document', 'localStorage', 'location',
  CODE + '\n;globalThis.__au={AU,AU_ST,alignZh,splitZhText,auSrtTime,auRender,auSeekCue,auFindActive,' +
  'auSyncActive,auStepCue,auSetView,auToggleBlind,auFmt,auLoadCues,auSave,auBoot,auCands,auOpenLocal,auPick};'
)(globalThis.window, globalThis.document, globalThis.localStorage, globalThis.location);

const A = globalThis.__au;

/* ---------- 1. 中文切句 ---------- */
ok(A.splitZhText('一。二！三？').length === 3, '一行多句按中文标点切开（3 句）');
ok(A.splitZhText('第一行\n第二行').length === 2, '按行切（2 句）');
ok(A.splitZhText('中文一\nHello world\n中文二').length === 2,
   '双语稿里纯英文行被跳过，只留中文（2 句）');
ok(A.splitZhText('').length === 0, '空文本 → 0 句');
ok(A.splitZhText('no chinese here').length === 0, '全是英文 → 0 句（不会误当译文）');

/* ---------- 2. 三种句数关系 ---------- */
function mk(n) {
  const texts = [
    'The city has changed a lot over the past decade.',
    'I still remember the small bookshop on the corner.',
    'Now it is a coffee shop.'
  ];
  return texts.slice(0, n).map((t, i) => ({ st: i * 4, et: i * 4 + 3.5, en: t, zh: '', i }));
}

// 2.1 句数相等 → 一一对应
let c = mk(3);
let r = A.alignZh(c, '城市变化很大。\n我还记得那家小书店。\n现在它是咖啡馆。');
ok(r.ok && c.every((x, i) => x.zh === ['城市变化很大。', '我还记得那家小书店。', '现在它是咖啡馆。'][i]),
   '中文 3 句 = 英文 3 句 → 逐句对齐');
ok(/逐句对齐/.test(r.note), '返回「逐句对齐」说明');

// 2.2 中文多 → 合并
c = mk(3);
r = A.alignZh(c, '城市变化很大。\n十年间什么都变了。\n我还记得小书店。\n店主会给我留报纸。\n现在它是咖啡馆。\n租金涨了三倍。');
ok(c.every(x => !!x.zh), '中文 6 句 > 英文 3 句 → 每句英文都有中文');
ok(c[0].zh.includes('城市变化很大') && c[0].zh.includes('十年间'), '多出的中文被合并进同一句英文');
ok(c.reduce((n, x) => n + (x.zh || '').length, 0) >= 30, '中文没有丢字（合并后总长正常）');

// 2.3 中文少 → 覆盖
c = mk(3);
r = A.alignZh(c, '这座城市变化很大，我还记得那家小书店。');
ok(c[0].zh && !c[1].zh && !c[2].zh, '中文 1 句 < 英文 3 句 → 只在首句显示');
ok(/覆盖/.test(r.note), '返回「一句覆盖多句」说明');

// 2.4 极端不匹配
c = mk(3);
r = A.alignZh(c, '');
ok(!r.ok, '没有中文 → 不匹配并返回原因');
c = [];
r = A.alignZh(c, '中文');
ok(!r.ok, '没有英文字幕 → 不匹配并返回原因');

/* ---------- 3. 时间轴查找 ---------- */
A.AU.cues = mk(3).map((x, i) => ({ st: [0, 4, 8][i], et: [3.5, 7.5, 11.5][i], en: x.en, zh: '', i }));
ok(A.auFindActive(0.0) === 0, 't=0 → 第 1 句');
ok(A.auFindActive(3.6) === 0, 't=3.6（句间空隙）→ 仍算第 1 句');
ok(A.auFindActive(4.0) === 1, 't=4.0 → 第 2 句');
ok(A.auFindActive(99) === 2, '超出末尾 → 停在第 3 句');
ok(A.auFindActive(-1) === -1, 't<0 → 无当前句');

/* ---------- 4. 点句跳播 ---------- */
audio.currentTime = 0; audio.paused = true; audio.played = 0;
A.auSeekCue(1);
ok(Math.abs(audio.currentTime - 4) < 1e-6, `点第 2 句 → currentTime=${audio.currentTime}（应为 4）`);
ok(audio.played > 0, '跳转后自动播放');
ok(A.AU.active === 1, '当前句索引同步为 1');
A.auStepCue(1);
ok(Math.abs(audio.currentTime - 8) < 1e-6, '「下一句」→ 跳到 8 秒');
A.auStepCue(-1);
ok(Math.abs(audio.currentTime - 4) < 1e-6, '「上一句」→ 回到 4 秒');
audio.currentTime = 4.2;
A.auSyncActive(true);
ok(A.AU.active === 1, '播放到 4.2s → 高亮切到第 2 句');

/* ---------- 5. 渲染 ---------- */
A.AU.cues = mk(3);
A.AU.cues[1].zh = '我还记得那家小书店。';
A.auRender();
const rows = (el('auSubs').innerHTML.match(/class="au-cue/g) || []).length;
ok(rows === 3, `渲染 3 行字幕（实际 ${rows}）`);
ok(el('auSubs').innerHTML.includes('我还记得那家小书店。'), '中文已渲染到第 2 行');
ok(el('auSubs').innerHTML.includes('（点这里补中文）'), '缺中文的行给出可点击提示');
A.auSetView('zh');
ok(el('auSubs').className.includes('zh-only'), '切「仅中文」→ 加 zh-only 类');
A.auSetView('both');
A.auToggleBlind();
ok(el('auSubs').className.includes('blind'), '盲听 → 加 blind 类（英文模糊）');
A.auToggleBlind();
ok(!el('auSubs').className.includes('blind'), '再点一次退出盲听');

/* ---------- 6. SRT ---------- */
ok(A.auSrtTime(0) === '00:00:00,000', '时间码 0 → 00:00:00,000');
ok(A.auSrtTime(4.12) === '00:00:04,120', `时间码 4.12 → ${A.auSrtTime(4.12)}`);
ok(A.auSrtTime(3671.5) === '01:01:11,500', `时间码 3671.5 → ${A.auSrtTime(3671.5)}`);
ok(A.auFmt(65.5) === '1:05.5', `界面时间 65.5 → ${A.auFmt(65.5)}`);

/* ---------- 7. HTML 元素齐全 ---------- */
const ids = new Set([...html.matchAll(/\bid="([^"]+)"/g)].map(m => m[1]));
['auFile', 'auLib', 'auZh', 'auZhFile', 'auSubs', 'auAsrBtn', 'auAsrMsg', 'auInfo',
 'auBridgeTip', 'auLoopOne', 'auView', 'auBlindBtn', 'auRate', 'auHeadCnt'].forEach(id => {
  ok(ids.has(id), `HTML 里存在 #${id}`);
});
const fns = new Set([...html.matchAll(/function\s+([A-Za-z_$][\w$]*)\s*\(/g)].map(m => m[1]));
const inline = new Set([...html.matchAll(/on(?:click|change)="([A-Za-z_$][\w$]*)\(/g)].map(m => m[1]));
const missing = [...inline].filter(f => !fns.has(f));
ok(missing.length === 0, '内联事件引用的函数都已定义' + (missing.length ? '：缺 ' + missing.join(',') : ''));

/* ---------- 8. 本机桥探测：连不上时必须给出结论和出路 ---------- */
(async function () {
  const loc = globalThis.location;

  // 8.1 本机直连版：只探同源
  loc.protocol = 'http:'; loc.hostname = '127.0.0.1'; loc.port = '8787'; loc.host = '127.0.0.1:8787';
  const c1 = A.auCands();
  ok(c1.length === 1 && c1[0] === '', '本机直连版 → 只探同源（1 个候选）');

  // 8.2 在线版：8787 / 8800 / 8899 一起排上
  loc.protocol = 'https:'; loc.hostname = 'www.workbuddy.cn'; loc.port = ''; loc.host = 'www.workbuddy.cn';
  const c2 = A.auCands();
  ok(c2.length === 3 && c2.includes('http://127.0.0.1:8787') && c2.includes('http://127.0.0.1:8800') &&
     c2.includes('http://127.0.0.1:8899'), '在线版 → 8787 / 8800 / 8899 三个端口都试（去重）');
  ok(c2.every(u => /^http:\/\/127\.0\.0\.1:\d+$/.test(u)), '在线版候选只指向 127.0.0.1（不会乱连外网）');

  // 8.3 在线版全失败：说清原因 + 给按钮，不能停在「正在检查」
  globalThis.fetch = () => Promise.reject(new Error('Failed to fetch'));
  await A.auBoot(1);
  await new Promise(r => setTimeout(r, 60));
  const tip = el('auBridgeTip').innerHTML;
  ok(/没连上本机桥/.test(tip), '在线版连不上 → 明确报「没连上本机桥」');
  ok(/在线版（https）/.test(tip), '在线版 → 指出是 https 拦截，不甩锅给用户');
  ok(/打开本机直连版/.test(tip) && /重试检测/.test(tip) && /改桥地址/.test(tip),
     '失败卡片给三个可操作按钮');
  ok(el('auBridgeTip').className.includes('bad'), '失败态用 bad 样式（橙色告警）');
  ok(A.AU_ST.probing === false, '失败后 probing 复位 → 可以重试，不会永久卡住');

  // 8.4 没连上时选文件不能白丢
  A.auPick({ target: { files: [{ name: 'demo.mp3', size: 999 }], value: 'x' } });
  ok(A.AU.pending && A.AU.pending.name === 'demo.mp3', '没连上桥时选的文件被暂存（连上自动上传）');
  A.AU.pending = null;

  // 8.5 「打开本机直连版」指向 8787
  let opened = '';
  globalThis.window.open = u => { opened = u; return null };
  A.auOpenLocal();
  ok(opened === 'http://127.0.0.1:8787/', `直连版按钮地址正确（${opened}）`);

  // 8.6 连上以后恢复正常提示
  globalThis.fetch = () => Promise.resolve({
    ok: true, status: 200,
    text: () => Promise.resolve(JSON.stringify({ ok: true, installed: true, model: 'base.en', modelCached: true, stored: 2 }))
  });
  await A.auBoot(1);
  await new Promise(r => setTimeout(r, 60));
  const tip2 = el('auBridgeTip').innerHTML;
  ok(/ASR 已就绪/.test(tip2), '连上 → 显示「ASR 已就绪」');
  ok(/已存 2 个音频/.test(tip2), '连上 → 显示本机音频库数量');
  ok(A.AU_ST.ok === true, 'AU_ST.ok 置位（后续上传放行）');
  ok(el('auBridgeTip').className.includes('ok'), '连上态用 ok 样式');

  console.log(`\n${fail === 0 ? '🎉' : '⚠️'} 本地音频精听：${pass} 通过 / ${fail} 失败`);
  process.exit(fail === 0 ? 0 : 1);
})();
