#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
repair.py — HeyGen Avatar IV 母帶「幀級修補」（OMNI 正典 v1）

修的是什麼：
  ★ 桌面／背景區的隨機爆白光斑（AI glow artifact）
    Avatar IV 偶爾會在桌面或設備燈上生出一團過曝白光，持續 0.1–0.5 秒。
    指標（多手團塊 / deskhand / faceid）全都抓不到，但肉眼一定看得見。

不修的是什麼（已實證為誤報，動了反而錯）：
  ✗ audit_逐幀稽核.py 的「≥3 團」——它的 ROI 從 y>900 開始，會把
    「下巴／脖子的膚色」和「桌面上的小亮點」誤判成多出來的手。
    2026-07-29 於 v30 實證：f584-586、f1036 全部是誤報。

方法：時間中位數背景還原 + 膚色保護 + 羽化 alpha 合成
  → 只動「比乾淨背景亮很多、且不是皮膚」的像素，手與臉一個像素都不碰。

用法：
  python3 repair.py in.mp4 out.mp4 [--debug debug.png] [--dry]
"""
import cv2, numpy as np, sys, os, json, subprocess, tempfile

BAND_Y      = 1300      # 只在這條 y 以下找光斑（桌面帶；臉/胸不碰）
OVER_TH     = 235       # 過曝像素亮度門檻
SEG_GAP     = 4         # 幀距 ≤ 此值視為同一段
NB          = 10        # 每段前後各取幾幀當乾淨背景
DIFF_TH     = 20        # 比背景亮多少才算光斑
ABS_TH      = 120       # 絕對亮度下限（避免把暗部雜訊當光斑）
SKIN_DILATE = 25        # 膚色保護帶（往外擴，確保手緣不被吃）
FEATHER     = 41        # 羽化核（奇數）
HALO_R      = 160       # 核心外擴多少 px 去吃柔光暈
SOFT_LO     = 5         # 連續 alpha 起點（比背景亮這麼多開始修）
SOFT_HI     = 28        # 連續 alpha 飽和點
BG_BRIGHT_GUARD = 145   # 乾淨背景本身就比這亮＝該處有內容，不碰


def skin_mask(bgr):
    ycc = cv2.cvtColor(bgr, cv2.COLOR_BGR2YCrCb)
    b, g, r = cv2.split(bgr.astype(np.int16))
    m = ((ycc[:, :, 1] > 133) & (ycc[:, :, 1] < 183) & (ycc[:, :, 2] > 72) &
         (ycc[:, :, 2] < 132) & (ycc[:, :, 0] > 80) & (r - b > 18) & (r - g > 6))
    return m.astype(np.uint8)


def detect(path):
    """回傳 (壞幀段清單, 每幀過曝像素數, 總幀數, fps)"""
    c = cv2.VideoCapture(path)
    fps = c.get(cv2.CAP_PROP_FPS) or 25.0
    counts = []
    while True:
        ok, f = c.read()
        if not ok:
            break
        g = cv2.cvtColor(f[BAND_Y:, :], cv2.COLOR_BGR2GRAY)
        counts.append(int((g > OVER_TH).sum()))
    c.release()
    a = np.array(counts)
    base = float(np.median(a)) if len(a) else 0.0
    th = max(base * 6.0, 800.0)
    bad = np.where(a > th)[0]
    segs = []
    if len(bad):
        s = p = bad[0]
        for x in bad[1:]:
            if x - p > SEG_GAP:
                segs.append((int(s), int(p)))
                s = x
            p = x
        segs.append((int(s), int(p)))
    return segs, a, len(counts), fps, base, th


def load_frames(path, idxs):
    idxs = set(idxs)
    out, i = {}, 0
    c = cv2.VideoCapture(path)
    while True:
        ok, f = c.read()
        if not ok:
            break
        if i in idxs:
            out[i] = f
        i += 1
    c.release()
    return out


def repair(path, outpath, debug=None, dry=False):
    segs, counts, n, fps, base, th = detect(path)
    rep = {"frames": n, "fps": fps, "overexposed_median": base,
           "threshold": th, "segments": []}
    for s, e in segs:
        rep["segments"].append({
            "f": [s, e], "t": [round(s / fps, 2), round(e / fps, 2)],
            "dur_s": round((e - s + 1) / fps, 2),
            "peak_px": int(counts[s:e + 1].max())})
    print(json.dumps(rep, ensure_ascii=False, indent=1))
    if not segs:
        print("✅ 沒有偵測到光斑，不需修補")
        return rep
    if dry:
        return rep

    badset = set()
    for s, e in segs:
        badset |= set(range(s, e + 1))

    need = set(badset)
    for s, e in segs:
        need |= {i for i in range(s - NB, s) if 0 <= i < n and i not in badset}
        need |= {i for i in range(e + 1, e + 1 + NB) if 0 <= i < n and i not in badset}
    F = load_frames(path, need)

    fixed, dbg = {}, []
    for s, e in segs:
        nb = [F[i] for i in list(range(s - NB, s)) + list(range(e + 1, e + 1 + NB))
              if i in F]
        if len(nb) < 4:
            print(f"⚠️ f{s}-{e} 鄰幀不足({len(nb)})，跳過")
            continue
        bg = np.median(np.stack([x[BAND_Y:, :] for x in nb]), axis=0).astype(np.uint8)
        bg_g = cv2.cvtColor(bg, cv2.COLOR_BGR2GRAY).astype(np.int16)
        for i in range(s, e + 1):
            f = F[i]
            band = f[BAND_Y:, :]
            g = cv2.cvtColor(band, cv2.COLOR_BGR2GRAY).astype(np.int16)
            m = (((g - bg_g) > DIFF_TH) & (g > ABS_TH)).astype(np.uint8)
            sk = cv2.dilate(skin_mask(band), np.ones((SKIN_DILATE, SKIN_DILATE), np.uint8))
            m = (m & (1 - sk)).astype(np.uint8)
            m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
            m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
            # 只留夠大的團（去雜訊）→ 這是「核心」，用來定位，不是最終遮罩
            nn, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
            keep = np.zeros_like(m)
            for j in range(1, nn):
                if st[j, cv2.CC_STAT_AREA] >= 600:
                    keep[lab == j] = 1
            if keep.sum() == 0:
                continue
            # ── 連續 alpha：核心之外還有一圈柔光暈，二值遮罩吃不掉 ──
            ys, xs = np.where(keep > 0)
            H, W = keep.shape
            y0, y1 = max(0, ys.min() - HALO_R), min(H, ys.max() + HALO_R)
            x0, x1 = max(0, xs.min() - HALO_R), min(W, xs.max() + HALO_R)
            roi = np.zeros((H, W), np.float32)
            roi[y0:y1, x0:x1] = 1.0
            excess = (g - bg_g).astype(np.float32)
            a = np.clip((excess - SOFT_LO) / float(SOFT_HI - SOFT_LO), 0, 1)
            a *= roi
            a[sk > 0] = 0                     # 皮膚一律不碰
            a[bg_g > BG_BRIGHT_GUARD] = 0     # 背景本來就亮的地方＝有內容，不碰
            a = cv2.GaussianBlur(a, (FEATHER, FEATHER), 0)
            a = np.clip(a, 0, 1)[:, :, None]
            newband = (band.astype(np.float32) * (1 - a) + bg.astype(np.float32) * a)
            out = f.copy()
            out[BAND_Y:, :] = newband.astype(np.uint8)
            fixed[i] = out
            if debug and len(dbg) < 4:
                vis = np.hstack([
                    cv2.resize(band, (300, 220)),
                    cv2.resize(cv2.cvtColor((a[:, :, 0] * 255).astype(np.uint8),
                                            cv2.COLOR_GRAY2BGR), (300, 220)),
                    cv2.resize(newband.astype(np.uint8), (300, 220))])
                cv2.putText(vis, f"f{i}  BEFORE | MASK | AFTER", (8, 22),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                dbg.append(vis)
    if debug and dbg:
        cv2.imwrite(debug, np.vstack(dbg))
        print("debug →", debug)

    # ── 寫檔：raw 幀直接 pipe 進 ffmpeg（單次編碼，不落地暫存檔）＋ 原音軌 ──
    c = cv2.VideoCapture(path)
    w = int(c.get(cv2.CAP_PROP_FRAME_WIDTH)); h = int(c.get(cv2.CAP_PROP_FRAME_HEIGHT))
    p = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error",
         "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}", "-r", str(fps), "-i", "-",
         "-i", path, "-map", "0:v:0", "-map", "1:a:0",
         "-c:v", "libx264", "-crf", "16", "-preset", "medium",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", outpath], stdin=subprocess.PIPE)
    i = 0
    while True:
        ok, f = c.read()
        if not ok:
            break
        p.stdin.write(fixed.get(i, f).tobytes())
        i += 1
    c.release(); p.stdin.close(); p.wait()
    rep["repaired_frames"] = sorted(fixed)
    print(f"✅ 修補 {len(fixed)} 幀 → {outpath}")
    return rep


if __name__ == "__main__":
    a = sys.argv[1:]
    dbg = a[a.index("--debug") + 1] if "--debug" in a else None
    dry = "--dry" in a
    pos = [x for x in a if not x.startswith("--") and x != dbg]
    repair(pos[0], pos[1] if len(pos) > 1 else "out_repaired.mp4", dbg, dry)
