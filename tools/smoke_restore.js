/* 冒烟测试：离线（桥不可用）时页面应回退到内置快照，显示 22 组词 + 1-4 组翻页卡 */
const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

const ROOT = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
// 期望组数直接从内置快照读，增组后测试不用改
const seedJson = JSON.parse(html.match(/<script[^>]*id="obs-seed"[^>]*>([\s\S]*?)<\/script>/)[1]);
const EXPECT_GROUPS = new Set(seedJson.words.map(w => w.grp)).size;
const EXPECT_WORDS = seedJson.words.length;

const dom = new JSDOM(html, {
  url: 'http://127.0.0.1:8787/',
  runScripts: 'dangerously',
  pretendToBeVisual: true,
  beforeParse(window) {
    window.fetch = (url) => {
      const u = String(url);
      if (u.indexOf('panels.json') >= 0) {
        const p = path.join(ROOT, 'img/passages/panels.json');
        const body = fs.readFileSync(p, 'utf8');
        return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(JSON.parse(body)) });
      }
      // 桥与资料库全部不可用，模拟离线
      return Promise.reject(new Error('offline'));
    };
  },
});

function wait(ms) { return new Promise(r => setTimeout(r, ms)); }

(async () => {
  await wait(2000);
  const w = dom.window, d = w.document;
  const chips = d.querySelectorAll('#psChips .chip');
  const chipText = Array.from(chips).map(c => c.textContent.trim());
  const cnt = d.getElementById('psCount');
  const buildTag = d.getElementById('buildTag');

  console.log('组 chips 数量:', chips.length, '（期望 '+EXPECT_GROUPS+' 组 / '+EXPECT_WORDS+' 词）');
  console.log('前 3 / 后 3:', chipText.slice(0, 3).join(' | '), '...', chipText.slice(-3).join(' | '));
  console.log('计数条:', cnt ? cnt.textContent.trim() : '(无)');
  console.log('构建标记:', buildTag ? buildTag.textContent.trim() : '(无)');

  let allOk = chips.length === EXPECT_GROUPS;

  for (const g of [1, 2, 3, 4]) {
    w.psPick(g);
    await wait(500);
    const img = d.querySelector('#psComic .pc-img');
    const dots = d.querySelectorAll('#psComic .pc-dots i');
    const src = img ? img.getAttribute('src') : '(未渲染)';
    console.log(`第 ${g} 组 → 图: ${src} | 圆点: ${dots.length} | 标题: ${(d.querySelector('#psComic .pc-cap .t') || {}).textContent}`);
    if (!img || dots.length !== 6 || src.indexOf(`/g${g}-1.webp`) < 0) allOk = false;
  }

  // 翻页到第 2 页
  w.pcGo(1);
  await wait(400);
  const img2 = d.querySelector('#psComic .pc-img');
  console.log('翻页后:', img2 ? img2.getAttribute('src') : '(无)');

  // 无插图卡的组应显示提示，而不是空白
  w.psPick(EXPECT_GROUPS);
  await wait(500);
  const hint = d.querySelector('#psComic .ps-comic-hint');
  console.log('末组提示:', hint ? hint.textContent.trim().slice(0, 60) + '…' : '(无提示)');
  if (!hint) allOk = false;

  const hasChips = d.querySelectorAll('#psChips .chip.ps-has').length;
  console.log('带插图标记的组:', hasChips, '(应为 4)');
  if (hasChips !== 4) allOk = false;

  console.log(allOk ? '✅ SMOKE PASS' : '❌ SMOKE FAIL');
  process.exit(allOk ? 0 : 1);
})();
