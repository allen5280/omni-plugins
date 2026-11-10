# happy4_pipeline｜《快樂四開關》可重跑產線

這些是 2026-11-10 那支成片實際用的腳本，原樣保留。工作資料夾用環境變數 `JOB_DIR` 指定（沒設就用目前資料夾）。

| 檔案 | 用途 |
|---|---|
| `cut.py` | 讀 Whisper 轉錄與頻帶能量，產生跳剪表與鏡頭表 `plan.json` |
| `plan.json`、`en.json`、`sfx_events.json` | 那支片的資料：逐句時間碼、鏡頭表、英文字幕、音效時間表（當範例與格式參考） |
| `fx3.html` | 畫布場景引擎：18 種 B-roll 場景、蒙格底圖與 HUD、`sub`（底部字幕）、`title`（上方金色標題） |
| `params.json` | 各版畫場景的紙色參數 |
| `render5.js` | 逐幀渲染 B-roll 片段（2160×3840、crf 10）。需要 `img/<名稱>_mg.png` |
| `recolor_plates.py` | 版畫原圖 → 去背、深藍墨換金色的 `_mg.png` |
| `render6.js` | 渲染兩條透明 PNG 序列：`band/`（底部字幕）與 `tband/`（上方金色標題）。金色句與隱藏句在檔案開頭的 `GOLD`、`HIDE` |
| `build3.py` | `python3 build3.py pieces`：真人段裁切、放大、暗角（crf 10），並寫出 `concat3.txt` |
| `final3.py` | `A`、`B` 各編一半母帶（疊兩條字幕帶，`CRF` 可用環境變數改），`mux` 接合並混音 |
| `mkdraft3.py` | 分層剪映草稿（需要 pyJianYingDraft 0.2.7） |
| `pack4c.py` | 把母帶切成可上傳的分段，並產生 Windows 安裝程式（柏維哥不喜歡這個做法，留作參考） |
| `download_page.html` | 下載頁：在瀏覽器裡抓各分段、核對 SHA-256、接成一個 mp4 存檔。改 `PARTS` 與 `NAME` 就能重用 |

執行順序：`cut.py` → 生圖＋`recolor_plates.py` → `render5.js` → `build3.py pieces` → `render6.js` → `final3.py A`、`B`、`mux`。

注意：
- 兩個渲染程序不要同時寫同一個資料夾。
- 檔案託管單檔上限約 150–200 MB，母帶要切段；下載頁必須放在能以 `file://` 或一般網頁開啟的地方，不能放 Artifact。
- 字體要先裝好：Noto Sans TC、Noto Serif TC、Playfair Display、JetBrains Mono。
