---
name: motion-fx-library
description: 柏維哥的「最高質感動畫特效資料庫」＋4K 逐幀渲染器。內含 30 個已逐幀拆解的特效（構成、逐幀時間、用途、做法）、參考片的節拍與殼層骨架、片尾 CTA 留言卡、真人口播 30% 混剪規則，以及可直接出 2160×3840 影片的特效引擎。當柏維哥說「加特效」「做動畫」「B-roll 動畫」「字卡」「數字動畫」「章節卡」「片頭」「片尾 CTA」「視覺鉤子」「質感再高一點」「參考這支片拆解」「把特效植入資料庫」「真人口播混剪」「蒙格那種做法」，或任何短影音需要設計／製作動態圖像、要拆解一支爆款參考片時觸發。剪短影音時要與剪映草稿產線搭配使用：本 Skill 負責產出特效片段，剪輯 Skill 負責排上時間軸。
---

# 🎞️ 動畫特效資料庫 × 4K 渲染器 v1

> 來源：2026-11-10 逐幀拆解「30 種 CLAUDE 動畫特效」參考片（1104 幀全看過）。
> 每新增一支參考片，就用 `scripts/teardown.py` 拆、把新特效寫進資料庫 —— 資料庫越大，可輪替的技巧越多。

## 0️⃣ 這個 Skill 給你什麼

| 檔案 | 內容 | 什麼時候讀 |
|---|---|---|
| `references/FX30_逐幀拆解資料庫.md` | 30 個特效：構成、逐幀動態、用途、做法路線、實作狀態；末尾有「依口播句型選特效」速查表 | 選特效、做特效之前 |
| `references/殼層節奏與CTA_拆解.md` | 33 幀節拍格、單鏡頭內部節奏、終端機殼層、片尾 CTA 時間表、色彩字體 | 排節奏、做片尾之前 |
| `references/真人口播混剪規則.md` | 真人 30%、開場必真人、哪些句子給真人、驗收清單 | 剪真人口播片之前 |
| `references/使用輪替紀錄.md` | 每支片用過哪些特效 | 開工前讀、完工後寫 |
| `references/蒙格片DNA_逐幀拆解.md` | **預設視覺與聲音基底**：背景、HUD、章節卡、雙語字幕座標、底部資訊列、聲音結構 | 每支片開工前 |
| `references/案例_快樂四開關_2026-11-10.md` | 第一支成片的完整流程、實測數字、踩到的坑 | 做真人口播混剪片之前 |
| `scripts/render_fx.js` ＋ `fx_engine.html` | 逐幀渲染器，9 個特效已實作 | 要出特效片段時 |
| `scripts/fx_presets.json` | 每個已實作特效的範例參數 | 改文字出片時 |
| `scripts/teardown.py` | 把新參考片拆成接觸表 | 柏維哥丟新參考片時 |

## 1️⃣ 工作流程

```
口播逐字稿（含逐句時間碼）
  │
  ├─ 1. 每句標類型 → 決定真人或 B-roll（真人口播混剪規則 §2）
  ├─ 2. B-roll 句依「用途速查表」選特效；避開最近兩支片用過的（使用輪替紀錄）
  ├─ 3. 量配樂拍點 → 定節拍格 → 每個特效長度取格長整數倍（殼層節奏 §6）
  ├─ 4. 出片：已實作的用 render_fx.js；未實作的照資料庫的做法路線製作
  ├─ 5. 每個片段出接觸表，用肉眼看過（指標會騙人）
  └─ 6. 交給剪輯層排上時間軸；完工後寫回使用輪替紀錄
```

## 2️⃣ 出一個特效（已實作的 9 個）

```bash
# 看有哪些
node scripts/render_fx.js --list

# 4K 直式成片（預設 --scale 2 ＝ 2160×3840、h264）
node scripts/render_fx.js --fx giant_numeral --params @scripts/fx_presets.json#giant_numeral --out out/numeral.mp4

# 自訂文字與長度（長度取節拍格的整數倍；參考片是 1.1 秒）
node scripts/render_fx.js --fx speed_echo_number --dur 2.2 \
  --params '{"label":"粉絲","value":"50","sub":"萬人以上","tag":"ALL PLATFORMS","caption":"這是我的目標"}' --out out/echo.mp4

# 進剪映用的中間檔／透明底
node scripts/render_fx.js --fx cta_comment --dur 3.9 --codec prores --out out/cta.mov
node scripts/render_fx.js --fx speed_echo_number --codec alpha --out out/echo_alpha.mov

# 先出幾張靜幀檢查版面，不用等整段渲染
node scripts/render_fx.js --fx spec_dossier --stills 0,0.3,0.6,1.0 --scale 1 --out out/check
```

| 特效名 | 對應 | 必填參數 |
|---|---|---|
| `light_blade_sting` | 01 光刃片頭 | `top` `glyph` `brand` |
| `speed_echo_number` | 05 殘影數字 | `label` `value` `sub`（可加 `swapAt`＋`next` 換第二組） |
| `giant_numeral` | 08 巨型數字 | `value` `kicker` `ticks` `at`（可加 `swapAt`＋`next`） |
| `spec_dossier` | 11 機密檔案 | `word` `file` `meta` `footer` |
| `porcelain_dial` | 12 瓷白錶盤 | `kicker` `label` `value` |
| `neon_chapter` | 21 霓虹章節 | `chips` `active` `title` `question` |
| `stamp_steps` | 27 郵票蓋章 | `h1` `h2` `steps` |
| `slots_counter` | 28 名額倒數 | `label` `from` `to` |
| `cta_comment` | 片尾 CTA 留言卡 | `keyword` `reply`（`--dur 3.9`） |

**環境**：node ≥ 18、`npm i playwright && npx playwright install chromium`、ffmpeg 在 PATH。雲端容器已內建 chromium。
**字體**：引擎會依序找 Noto Sans TC／思源黑體／微軟正黑體。要最接近參考片的質感，電腦要裝 **Noto Sans TC Black**（標題與數字）、**Noto Serif TC**（明體標題）、**Playfair Display**（巨型數字）。字體與品牌色可用 `--cfg '{"accent":"#FFD23F"}'` 覆寫。

## 3️⃣ 新增一個特效到引擎

在 `fx_engine.html` 的 `FX` 物件加一個函式，簽名固定為 `FX.名稱 = (參數, t秒, 總長秒) => { …畫到 g… }`。

- 畫布邏輯座標固定 1080×1920，不要寫死實體像素。
- **動畫只能是 `t` 的純函式**：不用 `Date`、不用 `Math.random()`（要亂數用內建的 `hash(n)`），否則重渲染會跳動。
- 內建工具：`T()` 畫字（支援模糊、外發光、描邊、字距）、`seg(t,起,迄,緩動)` 取 0–1 進度、`flash()` 開場閃白、`rr()` 圓角矩形、`cap()` 字幕行、`pick()` 處理 `swapAt` 換字。
- 寫完用 `--stills` 出 5 張靜幀看過，再把範例參數加進 `fx_presets.json`、把資料庫該條的狀態改成 ✅。

## 4️⃣ 拆解新參考片

```bash
python3 scripts/teardown.py 參考片.mp4 out/teardown            # 整個畫面
python3 scripts/teardown.py 參考片.mp4 out/teardown --crop 312:552:46:448   # 只看預覽窗
```

1. 先看 `cuts.txt`：鏡頭長度如果都是同一個數字（或它的整數倍），那就是節拍格。同明度的切點偵測不到，長度出現 2 倍、3 倍時代表中間有漏切。
2. 看 `overview_*.jpg` 理解結構，再看 `shot_*.jpg` 理解每個特效怎麼動。
3. 每個新特效依資料庫的格式寫一條（構成／逐幀／做法／用途），並分配做法路線 A–D。

## 5️⃣ 鐵律

1. **每個 B-roll 鏡頭前 3 幀就要有東西**，主體 0.4 秒內到位，中段換一次字或數字。
2. **B-roll 之間硬切**，不加溶接與滑動轉場；轉場感來自特效自己的進場。
3. **相鄰鏡頭明暗交替**；每屏中文不超過 12 字；一個鏡頭只有一個主體。
4. **中文字永遠用引擎疊**，不讓 AI 影片模型生中文字。
5. **同一支片特效不重複**，並避開最近兩支片用過的。
6. **數字必須是真的**。涉及收入、名額、人數的畫面加「示意」小字；金額標「潛力上限，非預期收入」；不出現保證、穩賺、月入多少這類用語。
7. **每個片段都要出接觸表用肉眼看**，再交給剪輯層。
9. **同一句話字體大小一律相同**，不做大小字混排（柏維哥 2026-11-10）。
10. **用內建 Bash 在本機做，不要用連接器沙盒逐步跑指令**；每一次連接器呼叫柏維哥都要手動按允許。非用不可時先報次數（細節見案例檔 v4）。
8. 這個 Skill 只產出特效片段，**不剪片、不上字幕、不調色** —— 那是剪輯產線的事。

## 6️⃣ 已知限制（如實記錄）

- 30 個特效中 9 個已實作並實測出片，21 個只有做法、尚未製作。資料庫裡每條都標了狀態。
- 參考片的音樂沒有聽過，1.1 秒節拍格是由畫面剪點量出來的；BPM 是推算值。
- 已實作的特效是依參考片重建的近似版，不是原檔。在這台雲端容器只有文泉驛正黑一種中文字重，粗細與參考片有落差；裝了上面列的字體後才會接近。
- 黏土、車削體、機械爆炸圖這類需要真實 3D 材質的特效（16、18、19、23、30）要靠 AI 生片當底，品質取決於生成結果，需要多抽幾次。
