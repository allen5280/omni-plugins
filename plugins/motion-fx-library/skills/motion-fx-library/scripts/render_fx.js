#!/usr/bin/env node
/* OMNI Motion FX 渲染器 v1
   用 Playwright 逐幀餵時間給 fx_engine.html，截圖直接 pipe 進 ffmpeg，零掉幀、零時間漂移。

   用法：
     node render_fx.js --fx speed_echo_number --params @presets.json#speed_echo_number --out out/echo.mp4
     node render_fx.js --list                      # 列出所有已實作特效
     node render_fx.js --fx giant_numeral --stills 0,0.2,0.6,1.0 --out out/stills   # 只出檢查用靜幀

   參數：
     --fx       特效名（fx_engine.html 內 FX 的 key）
     --params   JSON 字串，或 @檔案路徑，或 @檔案路徑#鍵名
     --dur      秒數（預設 1.1 ＝ 參考片的 33 幀節拍格）
     --fps      預設 30
     --scale    1 → 1080×1920；2 → 2160×3840（4K 直式，預設）
     --codec    h264（預設，直接可看）｜prores（進剪映／剪輯軟體用的中間檔）｜alpha（ProRes 4444 透明底）
     --cfg      JSON，覆寫引擎的字體／品牌色，例：'{"accent":"#FFD23F"}'
     --out      輸出 mp4/mov 路徑（--stills 時為資料夾）

   需求：node ≥ 18、playwright（npm i playwright && npx playwright install chromium）、ffmpeg 在 PATH。
   雲端容器已內建 chromium；若要指定瀏覽器路徑，設環境變數 PW_CHROMIUM。 */
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

function parseArgs(argv) {
  const a = {};
  for (let i = 2; i < argv.length; i++) {
    if (!argv[i].startsWith('--')) continue;
    const k = argv[i].slice(2);
    a[k] = argv[i + 1] && !argv[i + 1].startsWith('--') ? argv[++i] : true;
  }
  return a;
}
function loadJson(v, what) {
  if (!v || v === true) return {};
  try {
    if (v.startsWith('@')) {
      const [file, key] = v.slice(1).split('#');
      const j = JSON.parse(fs.readFileSync(file, 'utf8'));
      if (key && !(key in j)) throw new Error(`檔案裡找不到鍵「${key}」，現有：${Object.keys(j).join(', ')}`);
      return key ? j[key] : j;
    }
    return JSON.parse(v);
  } catch (e) {
    console.error(`✗ ${what} 讀取失敗：${e.message}`);
    process.exit(2);
  }
}

(async () => {
  const a = parseArgs(process.argv);
  const fps = Number(a.fps || 30), dur = Number(a.dur || 1.1), scale = Number(a.scale || 2);
  const codec = a.codec || 'h264', params = loadJson(a.params, '--params'), cfg = loadJson(a.cfg, '--cfg');
  const browser = await chromium.launch(process.env.PW_CHROMIUM ? { executablePath: process.env.PW_CHROMIUM } : {});
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: scale });
  await page.goto('file://' + path.join(__dirname, 'fx_engine.html'));
  await page.evaluate((c) => { Object.assign(window.CFG, c); return document.fonts.ready.then(() => true); }, cfg);

  if (a.list) {
    console.log((await page.evaluate(() => Object.keys(window.FX))).join('\n'));
    await browser.close(); return;
  }
  if (!a.fx || !a.out) { console.error('✗ 需要 --fx 與 --out（或用 --list 看有哪些特效）'); await browser.close(); process.exit(2); }
  const known = await page.evaluate(() => Object.keys(window.FX));
  if (!known.includes(a.fx)) { console.error(`✗ 沒有「${a.fx}」這個特效。可用：${known.join(', ')}`); await browser.close(); process.exit(2); }
  let ff = null; // 出錯時要能收掉 ffmpeg，否則行程會卡住不結束
  const draw = (t) => page.evaluate(([fx, p, tt, d]) => window.renderFrame(fx, p, tt, d), [a.fx, params, t, dur]);
  const shot = () => page.screenshot({ type: 'png', omitBackground: codec === 'alpha' });

  try {
    if (a.stills) {
      fs.mkdirSync(a.out, { recursive: true });
      for (const s of String(a.stills).split(',')) {
        await draw(Number(s));
        fs.writeFileSync(path.join(a.out, `${a.fx}_${Number(s).toFixed(2)}.png`), await shot());
      }
      console.log(`✓ 靜幀已輸出到 ${a.out}`);
    } else {
      fs.mkdirSync(path.dirname(path.resolve(a.out)), { recursive: true });
      const enc = codec === 'alpha' ? ['-c:v', 'prores_ks', '-profile:v', '4444', '-pix_fmt', 'yuva444p10le']
        : codec === 'prores' ? ['-c:v', 'prores_ks', '-profile:v', '3', '-pix_fmt', 'yuv422p10le']
        : ['-c:v', 'libx264', '-preset', 'slow', '-crf', '14', '-pix_fmt', 'yuv420p', '-movflags', '+faststart'];
      ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-', ...enc, '-r', String(fps), a.out], { stdio: ['pipe', 'inherit', 'inherit'] });
      const done = new Promise((res, rej) => { ff.on('close', (c) => (c === 0 ? res() : rej(new Error('ffmpeg 結束碼 ' + c)))); ff.on('error', rej); });
      const n = Math.round(dur * fps);
      for (let i = 0; i < n; i++) {
        await draw(i / fps);
        if (!ff.stdin.write(await shot())) await new Promise((r) => ff.stdin.once('drain', r));
      }
      ff.stdin.end(); await done;
      console.log(`✓ ${a.fx} → ${a.out}（${n} 幀，${1080 * scale}×${1920 * scale}，${codec}）`);
    }
  } catch (e) {
    console.error('✗ 渲染失敗：' + e.message.split('\n')[0]); process.exitCode = 1;
    if (ff && ff.exitCode === null) ff.kill('SIGKILL');
  } finally { await browser.close(); }
})();
