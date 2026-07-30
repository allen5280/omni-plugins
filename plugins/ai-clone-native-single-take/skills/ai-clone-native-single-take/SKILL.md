---
name: ai-clone-native-single-take
description: 柏維哥「AI 數字人原生單片」完美生產系統。從一段中文文案，全自動產出零瑕疵的數字人母帶（他的臉、他的克隆聲音、手會自然動、嘴型對得上、無多手無殘影無爆光斑），直接可進 B-roll／剪輯層。當柏維哥說「做數字人」「AI 複製人」「用我的臉做影片」「口播影片」「數字人母帶」「Avatar IV」「HeyGen 生片」「把這段文案變成影片」時觸發。也用於任何需要驗收既有數字人影片品質的時刻。
---

# 🎬 AI 數字人原生單片｜完美生產系統 v1

> 累積 15 輪失敗換來的正典。**每一條規則都有實測證據，不要憑直覺改。**

---

## 0️⃣ 一句話架構

```
✅ 唯一正確架構 ＝ HeyGen Avatar IV「原生單片」，一支到底，零合成
   → 結構上不可能有錯位／殘影／斷肢
❌ 任何形式的「換手／換部分肢體合成」都是死路（柏維哥兩度打回）
❌ 任何形式的「後處理消漂移」都是死路（指標變好、肉眼變差）
```

**柏維哥 2026-07-29 驗收原話**：「『零合成』這部影片已經近乎完美，我非常滿意！」

---

## 1️⃣ 五層管線（`scripts/omni_clone.py` 一鍵跑完）

```
文案 ─► L1 文案閘 ─► L2 克隆配音 ─► L3 數字人生成 ─► L4 全閘稽核 ─► L5 幀級修補 ─► 母帶
       ScriptDNA    MiniMax        HeyGen           量測+肉眼        光斑還原
                    speech-2.6-hd  Avatar IV
```

```bash
python3 scripts/omni_clone.py \
  --script script.txt \          # 中文文案（純文字，逗號分句）
  --base   perfect_v3.png \      # ★正典底圖（手部區乾淨＝不會爆光斑）
  --out    out/ \
  --keys   config/api_keys.txt
```

每一層都會停下來報告，任何一層沒過就不往下走。**不硬送。**

---

## 2️⃣ 正典參數（★一字不要改）

### L2 配音（MiniMax）
```
endpoint  https://api.minimax.io/v1/t2a_v2      ← Bearer sk-api-…，不需要 GroupId
model     speech-2.6-hd
voice_id  AllenDJIClone01
pitch 0 ｜ vol 1.0
speed     ❌ 不寫死 → 自動校準：speed × (6.42 ÷ 實測字秒率)，收斂在 1.16–1.26
字典      只放 MUST_FIX 命中的字（誰 著 塞 血 薄 率 差 曾 藏）
          ★「誰」必放 誰/(shei2)，否則唸成「水」
```

### L3 數字人（HeyGen Avatar IV）
```
POST https://api.heygen.com/v3/videos
{"type":"image","image":{"type":"asset_id","asset_id":<底圖>},
 "audio_asset_id":<音檔>,
 "aspect_ratio":"9:16","resolution":"1080p",   ← ★兩者必填，否則輸出 720×720
 "expressiveness":"high",                       ← ★唯一能讓桌上那隻手動起來的開關
 "motion_prompt": Z2_DESK}
```

**Z2_DESK 正典 prompt（乾淨桌面底圖用）**
```
The hand wearing the black watch, resting on the desk, keeps moving: it lifts a few centimetres
off the desk, the fingers spread open, then it settles back down onto the desk - over and over,
slowly and gently, all the way through. His facial features stay exactly as they are in the reference
photo. The camera is locked off and completely static.
```
> 有混音台的舊底圖，把三處 `desk` 換回 `mixing console`，**其餘一字不動**。

**成本**：US$3.00／分鐘（1080p）→ 52.5 秒 ＝ **US$2.63／支**。錢包制，先儲值。

---

## 3️⃣ 驗收閘與門檻

| 閘 | 指標 | 門檻 | v30 實測 |
|---|---|---|---|
| `gates.py audit` | 多手團塊 ≥3 | **0 幀** | 0 ✅ |
| `gates.py flare` | 桌面過曝峰值 | ≤ 中位數×6 | 修補後 610（原 14486）✅ |
| `gates.py faceid` | 身分保真（468 點 Procrustes）| ≤ 0.45 | 0.421 ✅ |
| `gates.py mouth` | 嘴型開口均值 | ≥ 0.032 | 0.0372 ✅ |
| `gates.py deskhand` | 桌手動能 | ≥ 底片×1.5 | 2.924（底片 1.288）✅ |
| **`sheet.py`** | **肉眼掃全片** | **★必跑，指標會騙人** | — |

```bash
python3 scripts/gates.py out/master.mp4
python3 scripts/sheet.py out/master.mp4 out/sheet.png 0 9999 18 8   # ★然後真的用眼睛看
```

### 🔴 已知的指標誤報（2026-07-29 實證，不要再被騙）
| 誤報 | 根因 | 已修正 |
|---|---|---|
| 「多手」f584-586 | ROI 從 y>900 開始，**下巴／脖子的膚色**被算成第三隻手 | 排除貼 ROI 上緣的團塊 |
| 「多手」f1036 | **桌面上的小亮點**（4183 px）被算成手 | MIN_AREA 2600→**8000**（真手 1% 分位數 9893）|
| 「瞬移幀」 | 團塊身分互換，原生底片都被判 1.9% | **整個指標作廢** |
| 15 秒探針 facegeo 比全片 | 窗口不同不可比 | 只比同長度 |

---

## 4️⃣ 🚫 死路總表（累積 15 輪，不要重走）

| 方向 | 結果 |
|---|---|
| 任何換手／換部分肢體合成 | ❌ 手臂比遮罩長、袖子是布不是膚色 → 斷肢 → 胸口硬邊錯位。柏維哥兩度打回 |
| 頭部消漂移後處理（destab）| ❌ 指標 22→7.8 很漂亮，柏維哥一看「完全不行」 |
| prompt 用 left/right 指認手 | ❌ 第三隻手的根因（模型用主角視角，與畫面左右相反）。改用「戴黑色手錶、放在桌上的那隻手」→ 多手 11.5%→0% |
| 同 prompt 重跑求 best-of-N | ❌ Avatar IV 近乎決定性，三個 take 差 <0.02 |
| 加「head and shoulders stay steady」| ❌ 全片多手暴增到 46 幀 |
| 約束詞鎖頭／頸／肩 | ❌ 會把手一起鎖死（動能掉到 1.0，比底片還低）。**只能鎖「五官」** |
| ★在 prompt 加光線描述 | ❌ Avatar IV 是 audio-driven，光已烘焙在底圖裡，加了不是沒作用就是動搖 identity lock。**光線描述屬於 B-roll 生成，不屬於這裡** |
| ★用 motion_control 做主口播 | ❌ 動作遷移不對嘴，會破壞 lip-sync。只能用在 B-roll |
| AI 修圖「移動」戒指 | ❌ 模型只會「加」不會「移」→ 兩個戒指。必須本機 `cv2.inpaint` 外科式修補 |
| 接力法（前段末幀當下一段 start）| ❌ 臉會二代漂移 |
| xfade 溶接兩段 | ❌ 雙臉疊影 |
| HeyGen `/v2/video/av4/generate` | ❌ 永遠 720×720，要用 `/v3/videos` |
| 音檔上傳寫 `audio/wav` | ❌ 被退 400543，必須 `audio/x-wav` |
| MiniMax 大量發音字典（18 條）| ❌ 關掉輕聲＋變調，慢 8.6%，就是「節奏怪怪的」元兇 |
| 寫死 TTS speed | ❌ 每段文案自然語速不同，必須用字秒率反推 |
| 文案留成語 | ❌ 觸發朗讀腔，提速時直接崩字（土法煉鋼→圖法鏈剛）|

---

## 5️⃣ 🧠 方法論鐵律

1. 使用者說「還是很嚴重」而指標說「已經比基準好」→ **一定是指標錯**
2. 修之前先量，量到能定位到幀
3. 先分清楚缺陷在「素材」還是「處理」
4. 失敗代價要落在人眼最不敏感的地方
5. **指標互相打架時，肉眼是唯一的地面真值**（每一版都要跑 `sheet.py`）
6. 模型的「幻覺」常是指令自相矛盾造成的 —— 先檢查 prompt 有沒有描述物理上不可能的狀態
7. **使用者的直覺經常比工程直覺正確**（柏維哥一句「假設是正常訓練這些都不該有問題」直接指出「合成必然切開肢體」的架構級缺陷）
8. **不完美的那幾秒**：連續 ≥0.5 秒 → B-roll 蓋掉；單幀／數幀 → **幀級修補**（不打斷 a-roll 的信任累積）

---

## 6️⃣ 交棒給 B-roll／剪輯層

這個 Skill 的產出是**母帶**（a-roll），不做 B-roll、不做字幕、不做調色。
母帶交出去時附帶 `master_report.json`：逐字稿＋逐句時間碼＋修補紀錄＋全閘數值，
下游（Claude Code 的 B-roll／剪映草稿產線）直接吃這份 JSON 排時間軸。

參考檔：
- `references/OMNI_數字人正典_v1.md` — 完整 DNA（底圖／文案／聲音／數字人／驗收／修補）
- `references/成本模型_每支影片攤提.md` — ★實查定價與規模攤提

---

## 7️⃣ 💰 成本速查

```
每支變動成本 ＝ HeyGen US$2.89 ＋ MiniMax US$0.28 ＝ US$3.17（≈NT$101）
Higgsfield 月訂閱攤提後：月產 30 支 → US$4.80/支；月產 100 支 → US$3.66/支
市場行情 60 秒口播 NT$180–360 → 我們便宜 40–72%，而且是本人的臉與聲音
★最大槓桿：a-roll 生一次出 9:16 + 1:1 + 16:9 三版本 → 等效 NT$51/支
```

---

## 8️⃣ 🏆 這套系統的終局

包成 **Skool 課程 ＋ Claude Code Plugin** 上架各大平台商轉。
因此所有腳本必須：參數外露成 config、不硬編碼個人 ID/路徑、
錯誤訊息寫人話、每個模組能獨立測試、文件寫成「別人照做也會成功」。
