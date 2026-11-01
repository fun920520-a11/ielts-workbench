/* 无头冒烟测试：验证页面在「桥已启动 / 桥未启动 / 同源直连版」三种情况下都能拿到数据 */
const fs = require('fs');

const PAGE = 'C:/Users/24277/WorkBuddy/2026-10-17-16-23-57/index.html';
const html = fs.readFileSync(PAGE, 'utf8');

const seedM = html.match(/<script[^>]*id="obs-seed"[^>]*>([\s\S]*?)<\/script>/);
const SEED = seedM ? seedM[1].trim() : '';

const blocks = [...html.matchAll(/<script(?![^>]*application\/json)[^>]*>([\s\S]*?)<\/script>/g)].map(m => m[1]);
const MAIN = blocks.sort((a, b) => b.length - a.length)[0];

// ---------- 场景选择 ----------
// USE_BRIDGE=1  → 桥在 8787（跨源，模拟 workbuddy.cn 打开的页面）
// LOCAL=1       → 同源直连版（页面由桥自己在 8899 提供）
// 都不设        → 无桥兜底
const LOCAL = process.env.LOCAL === '1';
const ORIGIN = LOCAL ? 'http://127.0.0.1:8899' : 'https://www.workbuddy.cn';
const winLoc = LOCAL
  ? { href: 'http://127.0.0.1:8899/', hostname: '127.0.0.1', port: '8899', host: '127.0.0.1:8899', protocol: 'http:' }
  : { href: 'https://www.workbuddy.cn/space/d/x', hostname: 'www.workbuddy.cn', port: '', host: 'www.workbuddy.cn', protocol: 'https:' };

function mkEl(id) {
  const el = {
    id, textContent: id === 'obs-seed' ? SEED : '', innerHTML: '', value: '', type: '', accept: '', style: {}, files: null,
    className: '', dataset: {}, children: [],
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
const document = {
  getElementById(id) { if (!els.has(id)) els.set(id, mkEl(id)); return els.get(id) },
  querySelector() { return null },
  querySelectorAll() { return [] },
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

const realFetch = globalThis.fetch;
function pageFetch(url, opt) {
  let u = String(url);
  if (u.startsWith('/')) u = ORIGIN + u;                 // 同源相对路径
  const local = /127\.0\.0\.1:(8787|8800|8899)/.test(u);
  if ((process.env.USE_BRIDGE === '1' || LOCAL) && local) return realFetch(u, opt);
  return Promise.reject(new TypeError('Failed to fetch'));
}

const win = { addEventListener() {}, removeEventListener() {}, location: winLoc };

globalThis.window = win;
globalThis.document = document;
globalThis.localStorage = localStorage;
globalThis.location = winLoc;
globalThis.fetch = pageFetch;
globalThis.URL.createObjectURL = () => 'blob:x';
globalThis.alert = () => {};
globalThis.prompt = () => null;
globalThis.confirm = () => true;
globalThis.navigator = { clipboard: { writeText: () => Promise.resolve() } };

const runner = new Function('window', 'document', 'localStorage', 'fetch', 'alert', 'prompt', 'confirm', 'navigator',
  MAIN + '\n;globalThis.__snap=function(){return {mode:OBS.mode,ready:OBS.ready,words:OBS.counts.words,episodes:OBS.counts.episodes,rules:(OBS.rules&&OBS.rules.items||[]).length,bridge:bridgeUrl()||"(同源相对路径)",WORDSlen:(typeof WORDS!=="undefined"?WORDS.length:0),LISTENlen:(typeof LISTEN!=="undefined"?LISTEN.length:0),chips:(document.getElementById("wGrpChips").innerHTML.match(/chip/g)||[]).length,build:(typeof APP_BUILD!=="undefined"?APP_BUILD:"(none)"),tag:document.getElementById("buildTag").textContent}};');

runner(win, document, localStorage, pageFetch, globalThis.alert, globalThis.prompt, globalThis.confirm, globalThis.navigator);

const wait = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  await wait((process.env.USE_BRIDGE === '1' || LOCAL) ? 4500 : 9000);
  const s = globalThis.__snap();
  console.log('MODE=' + (LOCAL ? 'same-origin(8899)' : (process.env.USE_BRIDGE === '1' ? 'bridge-up(8787)' : 'no-bridge')));
  console.log(JSON.stringify(s, null, 1));
  process.exit(0);
})();
