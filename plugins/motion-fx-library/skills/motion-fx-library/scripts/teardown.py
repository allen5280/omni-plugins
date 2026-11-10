#!/usr/bin/env python3
"""參考片逐幀拆解工具 —— 把一支爆款參考片變成「看得懂的接觸表」，供寫進特效資料庫。

用法：
    python3 teardown.py 參考片.mp4 輸出資料夾 [--crop W:H:X:Y] [--scene 0.12]

產出：
    cuts.txt            場景切點（秒）與相鄰間隔 —— 間隔如果都一樣，那就是節拍格
    overview_NN.jpg     全片總覽（每 12 幀一張），先看懂結構
    shot_NNN.jpg        每個鏡頭一條動態條（均勻取 11 幀），看懂單一特效怎麼動

--crop 只看畫面的一部分（例如參考片把特效放在小預覽窗裡），格式同 ffmpeg crop。
需求：ffmpeg / ffprobe 在 PATH、Pillow。
"""
import argparse
import glob
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"✗ 指令失敗：{' '.join(cmd[:3])} …\n{r.stderr[-400:]}")
    return r.stdout


def font(size=14):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "C:/Windows/Fonts/arialbd.ttf",
              "/System/Library/Fonts/Helvetica.ttc"):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def sheet(frames, fps, out, cols, tw):
    if not frames:
        return
    w0, h0 = Image.open(frames[0][1]).size
    th = round(tw * h0 / w0)
    rows = (len(frames) + cols - 1) // cols
    im = Image.new("RGB", (cols * tw, rows * (th + 18)), (20, 20, 20))
    dr, f = ImageDraw.Draw(im), font()
    for k, (idx, path) in enumerate(frames):
        x, y = (k % cols) * tw, (k // cols) * (th + 18)
        im.paste(Image.open(path).resize((tw, th), Image.LANCZOS), (x, y + 18))
        dr.text((x + 3, y + 1), f"f{idx} {(idx - 1) / fps:.2f}s", fill=(255, 220, 0), font=f)
    im.save(out, quality=86)


def main():
    ap = argparse.ArgumentParser(description="參考片逐幀拆解")
    ap.add_argument("video")
    ap.add_argument("outdir")
    ap.add_argument("--crop", help="W:H:X:Y，只拆解畫面的一部分")
    ap.add_argument("--scene", type=float, default=0.12, help="場景切換靈敏度，越小越敏感")
    a = ap.parse_args()
    if not os.path.exists(a.video):
        sys.exit(f"✗ 找不到影片：{a.video}")
    fdir = os.path.join(a.outdir, "frames")
    os.makedirs(fdir, exist_ok=True)

    num, den = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate",
                    "-of", "csv=p=0", a.video]).strip().split("/")
    fps = float(num) / float(den)
    vf = (f"crop={a.crop}," if a.crop else "") + "scale=360:-2"
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", a.video, "-vf", vf, "-q:v", "3", os.path.join(fdir, "f_%05d.jpg")])
    paths = sorted(glob.glob(os.path.join(fdir, "f_*.jpg")))
    n = len(paths)

    meta = os.path.join(a.outdir, "scene_raw.txt")
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", a.video, "-vf",
         f"select='gt(scene,{a.scene})',metadata=print:file={meta}", "-an", "-f", "null", "-"])
    cuts = [float(l.split("pts_time:")[1].split()[0]) for l in open(meta, encoding="utf-8") if "pts_time:" in l]
    bounds = [0.0] + cuts + [n / fps]
    with open(os.path.join(a.outdir, "cuts.txt"), "w", encoding="utf-8") as fh:
        fh.write(f"fps={fps:.3f} frames={n} duration={n / fps:.2f}s shots={len(bounds) - 1}\n")
        for i in range(len(bounds) - 1):
            fh.write(f"shot {i + 1:03d}  {bounds[i]:7.2f} → {bounds[i + 1]:7.2f}  長度 {bounds[i + 1] - bounds[i]:.2f}s"
                     f"（{round((bounds[i + 1] - bounds[i]) * fps)} 幀）\n")

    step, per = 12, 24
    ov = [(i + 1, paths[i]) for i in range(0, n, step)]
    for k in range(0, len(ov), per):
        sheet(ov[k:k + per], fps, os.path.join(a.outdir, f"overview_{k // per:02d}.jpg"), 8, 240)
    for i in range(len(bounds) - 1):
        s, e = int(bounds[i] * fps), max(int(bounds[i] * fps) + 1, int(bounds[i + 1] * fps) - 1)
        idx = sorted({min(n - 1, s + round((e - s) * j / 10)) for j in range(11)})
        sheet([(j + 1, paths[j]) for j in idx], fps, os.path.join(a.outdir, f"shot_{i + 1:03d}.jpg"), 11, 174)
    print(f"✓ {n} 幀、{len(bounds) - 1} 個鏡頭 → {a.outdir}（先看 cuts.txt 與 overview_*.jpg）")


if __name__ == "__main__":
    main()
