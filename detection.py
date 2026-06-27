# Section 2 - find the parked planes. Cut one plane out as a template, slide it
# over the image at a bunch of angles, and score how well it matches everywhere
# with normalized cross-correlation (written by hand).

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROT_MIN, ROT_MAX, ROT_STEP = -45, 45, 9   # angles to try, every 9 degrees
THRESHOLD = 0.46         # how good a match has to be to count as a plane
MIN_GAP = 36             # closest two separate planes can be (pixels)
MAX_PLANES = 14
WEIGHTS = (0.6, 0.2, 0.2)   # how much Y, Cb, Cr each count toward the score


def ncc(image, template, mask):
    # normalized cross-correlation, Gonzalez eq 12.2-8. Score is in [-1, 1] and
    # ignores overall brightness, so it matches shape - a plane in shadow still
    # matches one in the sun.
    image = image.astype(float)
    template = template.astype(float)
    th, tw = template.shape
    h, w = image.shape

    n = mask.sum()
    t_mean = (template * mask).sum() / n
    t0 = (template - t_mean) * mask        # zero-mean template
    t_energy = (t0 ** 2).sum()

    # top of the fraction: correlate image with the template, fast via the FFT
    F = np.fft.rfft2(image, (h, w))
    T = np.fft.rfft2(t0[::-1, ::-1], (h, w))    # flip so convolution == correlation
    top = np.fft.irfft2(F * T, (h, w))[th - 1:h, tw - 1:w]

    # bottom: how much the image varies under each window, via running sums
    s = _running_sum(image)
    s2 = _running_sum(image ** 2)
    win_sum = _box(s, th, tw)
    win_sq = _box(s2, th, tw)
    var = np.maximum(win_sq - win_sum ** 2 / (th * tw), 0)

    bottom = np.sqrt(t_energy * var)
    score = np.where(bottom > 1e-7, top / bottom, 0)
    return np.clip(score, -1, 1)


def _running_sum(a):
    s = np.cumsum(np.cumsum(a, 0), 1)
    return np.pad(s, ((1, 0), (1, 0)))


def _box(s, th, tw):
    # sum over every th x tw window using the running-sum table
    return s[th:, tw:] - s[:-th, tw:] - s[th:, :-tw] + s[:-th, :-tw]


def _rotate(channel, angle, fill):
    img = Image.fromarray(channel.astype(np.float32), "F")
    return np.asarray(img.rotate(angle, Image.BILINEAR, expand=True, fillcolor=fill), float)


def find_planes(image, template):
    # both image and template are YCbCr
    h, w = image.shape[:2]
    best = np.full((h, w), -1.0)
    hits = []

    for angle in range(ROT_MIN, ROT_MAX + 1, ROT_STEP):
        # rotate each channel; the mask marks the real pixels vs the blank corners
        # the rotation adds, so those corners don't mess up the score
        chans = [_rotate(template[..., c], angle, float(template[..., c].mean())) for c in range(3)]
        mask = (_rotate(np.ones(template.shape[:2]), angle, 0) > 0.5).astype(float)
        th, tw = mask.shape

        score = sum(WEIGHTS[c] * ncc(image[..., c], chans[c], mask) for c in range(3))

        # the score map is anchored at the window's top-left; shift to its centre
        oy, ox = th // 2, tw // 2
        gh, gw = score.shape
        np.maximum(best[oy:oy + gh, ox:ox + gw], score, out=best[oy:oy + gh, ox:ox + gw])

        ys, xs = np.where(score >= THRESHOLD)
        for y, x in zip(ys, xs):
            hits.append((score[y, x], y + oy, x + ox, angle))

    return _dedupe(hits), best


def _dedupe(hits):
    # one plane lights up a whole blob of pixels - keep only the strongest per area
    hits.sort(reverse=True)
    kept = []
    for score, y, x, angle in hits:
        if all((y - ky) ** 2 + (x - kx) ** 2 >= MIN_GAP ** 2 for _, ky, kx, _ in kept):
            kept.append((score, y, x, angle))
        if len(kept) >= MAX_PLANES:
            break
    return kept


def draw(rgb, hits, box=None, r=18):
    img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB")
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except Exception:
        font = ImageFont.load_default()

    if box:
        d.rectangle(box, outline=(0, 255, 255), width=2)
        d.text((box[0], box[1] - 16), "template", fill=(0, 255, 255), font=font)
    for i, (score, y, x, angle) in enumerate(hits, 1):
        d.ellipse([x - r, y - r, x + r, y + r], outline=(255, 0, 0), width=3)
        d.text((x + r + 2, y - r), str(i), fill=(255, 255, 0), font=font)
    return img
