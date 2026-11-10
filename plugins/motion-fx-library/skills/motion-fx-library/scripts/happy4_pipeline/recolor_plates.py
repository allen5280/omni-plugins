"""Turn the cream-paper linocut plates into transparent gold-on-dark plates for the Munger base.
Usage: python3 recolor_plates.py img/monkey.png img/lobster.png ...   ->  img/<name>_mg.png (3x upscaled, RGBA)"""
import sys
import numpy as np
from PIL import Image

for path in sys.argv[1:]:
    im = Image.open(path).convert('RGB')
    a = np.asarray(im).astype(float)
    # paper colour = mean of the four corners
    paper = np.concatenate([a[:40, :40].reshape(-1, 3), a[:40, -40:].reshape(-1, 3),
                            a[-40:, :40].reshape(-1, 3), a[-40:, -40:].reshape(-1, 3)]).mean(0)
    dist = np.sqrt(((a - paper) ** 2).sum(2))
    alpha = np.clip((dist - 22) / 70, 0, 1)            # paper becomes transparent
    r, b = a[..., 0], a[..., 2]
    lum = a.mean(2)
    navy = (b > r) & (lum < 115)                        # the navy ink
    out = np.clip(a * 1.12, 0, 255)
    out[navy] = np.array([236, 214, 160])               # navy ink -> champagne gold
    alpha = np.where(navy, np.clip((150 - lum) / 80, 0.35, 1) * np.clip(dist / 60, 0, 1), alpha)
    rgba = np.dstack([out, alpha * 255]).astype(np.uint8)
    dst = path.rsplit('.', 1)[0] + '_mg.png'
    Image.fromarray(rgba, 'RGBA').resize((im.width * 3, im.height * 3), Image.LANCZOS).save(dst)
    print('wrote', dst)
