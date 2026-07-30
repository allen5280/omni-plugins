#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
omni_clone.py — ★一鍵管線：中文文案 → 完美 AI 數字人母帶（OMNI 正典 v1）

    文案 → L1 文案閘 → L2 克隆配音 → L3 Avatar IV → L4 全閘稽核 → L5 幀級修補 → 母帶

用法：
    python3 omni_clone.py --script script.txt --base perfect_v3.png --out out/ \
                          --keys config/api_keys.txt [--seconds 52] [--yes]

金鑰檔需要（key=value 一行一個）：
    HEYGEN_API_KEY=  MINIMAX_API_KEY=  MINIMAX_VOICE_ID_DJI_CLONE=

任何一層沒過就停下來報告，不硬送。加 --yes 才會在 L1 有警告時仍繼續。
"""
import argparse, json, os, re, subprocess, sys, time, urllib.request, urllib.error, statistics

TARGET_CPS = 6.42
MUST_FIX = {"誰": "shei2", "著": "zhe5", "塞": "sai1", "血": "xue3", "薄": "bao2",
            "率": "lv4", "差": "cha1", "曾": "ceng2", "藏": "cang2"}
IDIOM = re.compile(r"[一-鿿]{4}")
Z2_DESK = ("The hand wearing the black watch, resting on the desk, keeps moving: it lifts a few centimetres "
           "off the desk, the fingers spread open, then it settles back down onto the desk - over and over, "
           "slowly and gently, all the way through. His facial features stay exactly as they are in the reference "
           "photo. The camera is locked off and completely static.")
IDIOM_BLACKLIST = ["土法煉鋼", "慘不忍睹", "逢人就講", "一氣呵成", "不勝枚舉", "焦頭爛額",
                   "水到渠成", "事半功倍", "無往不利", "刻不容緩", "望塵莫及", "捉襟見肘"]


def load_keys(p):
    kv = {}
    for l in open(p, encoding="utf-8-sig"):
        if "=" in l and not l.strip().startswith("#"):
            k, v = l.split("=", 1)
            kv[k.strip()] = v.strip()
    return kv


def http(url, method="GET", payload=None, headers=None, raw=None, timeout=300):
    h = dict(headers or {})
    data = None
    if payload is not None:
        data = json.dumps(payload).encode(); h["Content-Type"] = "application/json"
    if raw is not None:
        data = raw
    r = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        return json.loads(urllib.request.urlopen(r, timeout=timeout).read().decode())
    except urllib.error.HTTPError as e:
        return {"__err": e.code, "__body": e.read().decode(errors="replace")[:600]}


# ────────────────────────────── L1 文案閘 ──────────────────────────────
def hanzi(s):
    return re.findall(r"[一-鿿]", s)


def l1_gate(text, seconds=None):
    clean = re.sub(r"\s+", "", text)
    sents = [s for s in re.split(r"[，,。！!？?；;\n]", clean) if s]
    lens = [len(hanzi(s)) for s in sents if hanzi(s)]
    n = len(hanzi(clean))
    sigma = statistics.pstdev(lens) if len(lens) > 1 else 0.0
    idioms = [w for w in IDIOM_BLACKLIST if w in clean]
    q = clean.count("？") + clean.count("?")
    bad_len = [(i + 1, l) for i, l in enumerate(lens) if not (8 <= l <= 14)]
    poly = sorted({c for c in clean if c in MUST_FIX})
    rep = {
        "hanzi": n, "sentences": len(lens), "lens": lens,
        "sigma": round(sigma, 2), "sigma_gate": "≤2.2", "sigma_pass": sigma <= 2.2,
        "idioms": idioms, "idiom_pass": not idioms,
        "questions": q, "question_pass": q == 0,
        "out_of_range_sentences": bad_len, "len_pass": not bad_len,
        "est_seconds": round(n / TARGET_CPS, 2),
        "pron_dict": [f"{c}/({MUST_FIX[c]})" for c in poly],
    }
    if seconds:
        want = round(TARGET_CPS * seconds)
        rep["target_hanzi"] = want
        rep["hanzi_delta"] = n - want
        rep["hanzi_pass"] = abs(n - want) <= max(3, round(want * 0.05))
    rep["pass"] = all(rep[k] for k in rep if k.endswith("_pass"))
    return rep


# ────────────────────────────── L2 克隆配音 ──────────────────────────────
def tts(text, keys, outdir, takes=3):
    url = "https://api.minimax.io/v1/t2a_v2"
    hdr = {"Authorization": f"Bearer {keys['MINIMAX_API_KEY']}"}
    vid = keys["MINIMAX_VOICE_ID_DJI_CLONE"]
    pron = [f"{c}/({MUST_FIX[c]})" for c in sorted({c for c in text if c in MUST_FIX})]
    n = len(hanzi(text))

    def gen(speed, tag):
        body = {"model": "speech-2.6-hd", "text": text, "stream": False,
                "voice_setting": {"voice_id": vid, "speed": speed, "vol": 1.0, "pitch": 0},
                "audio_setting": {"sample_rate": 32000, "bitrate": 128000,
                                  "format": "mp3", "channel": 1}}
        if pron:
            body["pronunciation_dict"] = {"tone": pron}
        d = http(url, "POST", body, hdr)
        au = (d.get("data") or {}).get("audio")
        if not au:
            raise RuntimeError(f"TTS 失敗: {json.dumps(d, ensure_ascii=False)[:300]}")
        p = os.path.join(outdir, f"voice_{tag}.mp3")
        open(p, "wb").write(bytes.fromhex(au))
        ms = d["extra_info"]["audio_length"]
        return p, ms / 1000.0

    # 校準：speed=1.0 測一次 → 反推
    p0, s0 = gen(1.0, "cal")
    cps0 = n / s0
    speed = round(max(0.7, min(1.6, TARGET_CPS / cps0)), 3)
    print(f"  [L2] 校準：{n} 字 / {s0:.2f}s = {cps0:.2f} cps @speed1.0 → speed={speed}")
    best = None
    for i in range(takes):
        p, s = gen(speed, f"t{i+1}")
        cps = n / s
        print(f"  [L2] take{i+1}: {s:.2f}s  {cps:.2f} cps  Δ{abs(cps-TARGET_CPS):.3f}")
        if best is None or abs(cps - TARGET_CPS) < best[2]:
            best = (p, s, abs(cps - TARGET_CPS), cps)
    print(f"  [L2] ★選用 {os.path.basename(best[0])}  {best[1]:.2f}s  {best[3]:.2f} cps")
    wav = os.path.join(outdir, "voice.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", best[0],
                    "-ar", "48000", "-ac", "1", wav], check=True)
    return wav, best[1], speed, pron


# ────────────────────────────── L3 Avatar IV ──────────────────────────────
def heygen(wav, base_png, keys, outdir, prompt=Z2_DESK):
    H = {"X-Api-Key": keys["HEYGEN_API_KEY"]}
    bal = http("https://api.heygen.com/v3/users/me", headers=H)
    usd = ((bal.get("data") or {}).get("wallet") or {}).get("remaining_balance")
    print(f"  [L3] HeyGen 錢包餘額 US${usd}")
    a = http("https://upload.heygen.com/v1/asset", "POST", raw=open(wav, "rb").read(),
             headers={**H, "Content-Type": "audio/x-wav"})          # ★不能寫 audio/wav
    aid = (a.get("data") or {}).get("id")
    im = http("https://upload.heygen.com/v1/asset", "POST", raw=open(base_png, "rb").read(),
              headers={**H, "Content-Type": "image/png"})
    iid = (im.get("data") or {}).get("id")
    if not (aid and iid):
        raise RuntimeError(f"素材上傳失敗 audio={a} image={im}")
    print(f"  [L3] audio_asset={aid}  image_asset={iid}")
    g = http("https://api.heygen.com/v3/videos", "POST", {
        "type": "image", "image": {"type": "asset_id", "asset_id": iid},
        "audio_asset_id": aid, "aspect_ratio": "9:16", "resolution": "1080p",
        "expressiveness": "high", "motion_prompt": prompt}, H)
    vid = (g.get("data") or {}).get("video_id")
    if not vid:
        raise RuntimeError(f"生成請求失敗 {json.dumps(g, ensure_ascii=False)[:400]}")
    print(f"  [L3] video_id={vid} 渲染中…")
    for _ in range(120):
        time.sleep(10)
        d = http(f"https://api.heygen.com/v1/video_status.get?video_id={vid}", headers=H)["data"]
        if d["status"] == "completed":
            out = os.path.join(outdir, "master_raw.mp4")
            urllib.request.urlretrieve(d["video_url"], out)
            print(f"  [L3] ✅ 完成 {d['duration']:.2f}s → {out}")
            return out, vid, aid, iid
        if d["status"] == "failed" or d.get("error"):
            raise RuntimeError(f"生成失敗 {d.get('error')}")
    raise RuntimeError("渲染逾時（20 分鐘）")


# ────────────────────────────── 主流程 ──────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--out", default="out")
    ap.add_argument("--keys", required=True)
    ap.add_argument("--seconds", type=float, default=None)
    ap.add_argument("--yes", action="store_true")
    ap.add_argument("--skip-tts", default=None, help="已有音檔就直接給 wav 路徑")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    keys = load_keys(a.keys)
    text = open(a.script, encoding="utf-8").read().strip()
    here = os.path.dirname(os.path.abspath(__file__))
    report = {}

    print("\n【L1】文案閘")
    g1 = l1_gate(text, a.seconds); report["L1"] = g1
    print(json.dumps(g1, ensure_ascii=False, indent=1))
    if not g1["pass"]:
        print("\n❌ L1 沒過。修法：")
        if not g1["sigma_pass"]:
            print(f"   · 句長標準差 {g1['sigma']} > 2.2 → 把句長拉齊到 9–13 字")
        for i, l in g1["out_of_range_sentences"]:
            print(f"   · 第 {i} 句 {l} 字（要 8–14）")
        if g1["idioms"]:
            print(f"   · 成語 {g1['idioms']} → 換成口語（成語會觸發朗讀腔，提速時崩字）")
        if g1["questions"]:
            print("   · 有問號 → 改寫成內心話陳述")
        if "hanzi_delta" in g1:
            print(f"   · 字數 {g1['hanzi']}，目標 {g1['target_hanzi']}（差 {g1['hanzi_delta']:+d}）")
        if not a.yes:
            sys.exit(1)
        print("   （--yes 已指定，繼續）")

    print("\n【L2】克隆配音")
    if a.skip_tts:
        wav, dur = a.skip_tts, None
        print(f"  沿用既有音檔 {wav}")
    else:
        wav, dur, speed, pron = tts(text, keys, a.out)
        report["L2"] = {"wav": wav, "seconds": dur, "speed": speed, "pron_dict": pron}

    print("\n【L3】Avatar IV 生成")
    raw, vid, aid, iid = heygen(wav, a.base, keys, a.out)
    report["L3"] = {"video_id": vid, "audio_asset": aid, "image_asset": iid, "raw": raw}

    print("\n【L4】全閘稽核")
    r = subprocess.run([sys.executable, os.path.join(here, "gates.py"), raw,
                        "--json", os.path.join(a.out, "gates.json")],
                       capture_output=True, text=True)
    print(r.stdout[-2500:])
    report["L4"] = json.load(open(os.path.join(a.out, "gates.json"), encoding="utf-8"))

    print("\n【L5】幀級修補")
    final = os.path.join(a.out, "master.mp4")
    sys.path.insert(0, here)
    import repair
    rep = repair.repair(raw, final)
    report["L5"] = rep
    if not rep.get("segments"):
        subprocess.run(["cp", raw, final])
        print("  無光斑，母帶＝原生輸出")

    sheet = os.path.join(a.out, "sheet.png")
    subprocess.run([sys.executable, os.path.join(here, "sheet.py"), final, sheet,
                    "0", "99999", "18", "8"])
    report["sheet"] = sheet
    json.dump(report, open(os.path.join(a.out, "master_report.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    print(f"\n✅ 母帶 → {final}")
    print(f"📋 報告 → {os.path.join(a.out,'master_report.json')}")
    print(f"👁️  ★最後一步：打開 {sheet} 用肉眼掃一遍。指標會騙人，眼睛不會。")


if __name__ == "__main__":
    main()
