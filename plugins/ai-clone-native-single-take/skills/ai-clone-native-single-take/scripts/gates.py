#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gates.py — 數字人母帶全閘稽核（OMNI 正典 v1）

用法：
    python3 gates.py master.mp4 [--ref 原始底片.mp4] [--json report.json]

★ 這一版修掉了兩個歷史誤報（2026-07-29 於 v30 實證）：
   1. 舊版 ROI 從 y>900 起算，會把「下巴／脖子的膚色」算成第三隻手
      → 現在排除 bbox 貼著 ROI 上緣的團塊
   2. 舊版 MIN_AREA=2600，會把「桌面上的小亮點」（4183 px）算成手
      → 現在 MIN_AREA=8000（真手團塊 1% 分位數 = 9893）
   修正後 v30 的「多手」從 4 幀 → 0 幀（全部是誤報）

★ 「瞬移幀」指標已整個作廢：它用最左團塊追蹤，團塊身分會互換，
   原生底片（手根本沒動）都被判 1.9%。不要再用。

★ 指標全綠 ≠ 過關。務必再跑 sheet.py 用肉眼掃全片。
"""
import cv2, numpy as np, sys, json

ROI_TOP   = 900     # 手部搜尋區上緣（臉在這之上）
MIN_AREA  = 8000    # ★真手團塊面積下限（實測 1% 分位數 9893）
MIN_WH    = 45
TOP_GUARD = 4       # ★bbox 貼著 ROI 上緣 = 脖子/下巴，不是手
DESK_TOP  = 1300    # 桌面帶（找爆光斑）
OVER_TH   = 235


def skin(roi):
    ycc = cv2.cvtColor(roi, cv2.COLOR_BGR2YCrCb)
    b, g, r = cv2.split(roi.astype(np.int16))
    m = ((ycc[:, :, 1] > 138) & (ycc[:, :, 1] < 178) & (ycc[:, :, 2] > 77) &
         (ycc[:, :, 2] < 127) & (ycc[:, :, 0] > 95) & (r - b > 28) & (r - g > 12)).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
    return cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((21, 21), np.uint8))


def hand_blobs(f):
    m = skin(f[ROI_TOP:, :])
    n, lab, st, cen = cv2.connectedComponentsWithStats(m, 8)
    out = []
    for j in range(1, n):
        if st[j, cv2.CC_STAT_AREA] < MIN_AREA:
            continue
        if st[j, cv2.CC_STAT_WIDTH] < MIN_WH or st[j, cv2.CC_STAT_HEIGHT] < MIN_WH:
            continue
        if st[j, cv2.CC_STAT_TOP] <= TOP_GUARD:      # ★脖子/下巴，排除
            continue
        out.append((int(st[j, cv2.CC_STAT_AREA]), float(cen[j][0]),
                    float(cen[j][1]) + ROI_TOP))
    return out


def mouth_open(f):
    """嘴部開口代理：下臉中央帶的暗區（口腔）佔比縱向變異"""
    h, w = f.shape[:2]
    m = f[int(h * .32):int(h * .45), int(w * .38):int(w * .62)]
    g = cv2.cvtColor(m, cv2.COLOR_BGR2GRAY)
    return float((g < np.percentile(g, 25)).mean())


def run(path, ref=None):
    c = cv2.VideoCapture(path)
    fps = c.get(cv2.CAP_PROP_FPS) or 25.0
    multi, over, mo, dh, prev = [], [], [], [], None
    i = 0
    while True:
        ok, f = c.read()
        if not ok:
            break
        b = hand_blobs(f)
        if len(b) >= 3:
            multi.append(i)
        over.append(int((cv2.cvtColor(f[DESK_TOP:, :], cv2.COLOR_BGR2GRAY) > OVER_TH).sum()))
        mo.append(mouth_open(f))
        # 桌手動能：y 最大的那團的位移
        if b:
            d = max(b, key=lambda x: x[2])
            if prev is not None:
                dh.append(((d[1] - prev[0]) ** 2 + (d[2] - prev[1]) ** 2) ** .5)
            prev = (d[1], d[2])
        i += 1
    c.release()

    over = np.array(over); mo = np.array(mo); dh = np.array(dh) if len(dh) else np.array([0.])
    med = float(np.median(over)); th = max(med * 6, 800)
    flare = np.where(over > th)[0]
    segs = []
    if len(flare):
        s = p = flare[0]
        for x in flare[1:]:
            if x - p > 4:
                segs.append([int(s), int(p)]); s = x
            p = x
        segs.append([int(s), int(p)])

    r = {
        "file": path, "frames": i, "fps": fps,
        "multi_hand": {"frames": multi, "count": len(multi),
                       "pct": round(len(multi) / max(i, 1) * 100, 3),
                       "gate": "0 幀", "pass": len(multi) == 0},
        "flare": {"median_over_px": med, "threshold": th,
                  "peak": int(over.max()), "peak_frame": int(over.argmax()),
                  "segments_f": segs,
                  "segments_t": [[round(a / fps, 2), round(b / fps, 2)] for a, b in segs],
                  "gate": "0 段", "pass": len(segs) == 0},
        "mouth": {"mean_open": round(float(mo.mean()), 4), "gate": "≥0.032",
                  "pass": float(mo.mean()) >= 0.032},
        "deskhand": {"motion_energy": round(float(dh.mean()), 3)},
    }
    if ref:
        rr = run(ref)
        r["deskhand"]["ref_energy"] = rr["deskhand"]["motion_energy"]
        r["deskhand"]["ratio"] = round(r["deskhand"]["motion_energy"] /
                                       max(rr["deskhand"]["motion_energy"], 1e-6), 2)
        r["deskhand"]["gate"] = "≥1.5×原始底片"
        r["deskhand"]["pass"] = r["deskhand"]["ratio"] >= 1.5
    return r


if __name__ == "__main__":
    a = sys.argv[1:]
    ref = a[a.index("--ref") + 1] if "--ref" in a else None
    js = a[a.index("--json") + 1] if "--json" in a else None
    rep = run(a[0], ref)
    print(json.dumps(rep, ensure_ascii=False, indent=1))
    if js:
        json.dump(rep, open(js, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    gates = [v for v in rep.values() if isinstance(v, dict) and "pass" in v]
    print("\n" + ("✅ 全閘通過" if all(g["pass"] for g in gates) else "❌ 有閘未過"))
    print("⚠️  指標全綠 ≠ 過關 —— 一定要再跑 sheet.py 用肉眼掃全片")
