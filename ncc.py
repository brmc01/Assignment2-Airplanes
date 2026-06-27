"""
Section 2: normalized cross-correlation (Gonzalez & Woods, eq. 12.2-8).

The score is normalized to [-1, 1] and ignores overall brightness, so it matches
shape rather than intensity. The fast version computes the numerator with the FFT
and the local means/variances with integral images.
"""

import numpy as np


def _integral_image(channel):
    s = np.cumsum(np.cumsum(channel, axis=0), axis=1)
    return np.pad(s, ((1, 0), (1, 0)), mode="constant")


def _box_sums(integral, th, tw):
    a = integral[th:, tw:]
    b = integral[:-th, tw:]
    c = integral[th:, :-tw]
    d = integral[:-th, :-tw]
    return a - b - c + d


def normalized_cross_correlation(image, template, mask=None, eps=1e-7):
    # Returns the score map; entry (y, x) scores the window with top-left (y, x).
    image = image.astype(np.float64)
    template = template.astype(np.float64)
    th, tw = template.shape

    if mask is None:
        mask = np.ones_like(template)
    n = mask.sum()

    w_bar = (template * mask).sum() / n
    w0 = (template - w_bar) * mask          # zero-mean template
    sum_w0_sq = (w0 ** 2).sum()

    # Numerator = correlation of image with w0, done via FFT.
    h, w = image.shape
    F = np.fft.rfft2(image, (h, w))
    W = np.fft.rfft2(w0[::-1, ::-1], (h, w))   # flip -> correlation
    corr_full = np.fft.irfft2(F * W, (h, w))
    numerator = corr_full[th - 1:h, tw - 1:w]

    # Local variance of the image under each window, via integral images.
    integral = _integral_image(image)
    integral_sq = _integral_image(image ** 2)
    local_sum = _box_sums(integral, th, tw)
    local_sum_sq = _box_sums(integral_sq, th, tw)

    local_var = local_sum_sq - (local_sum ** 2) / (th * tw)
    local_var = np.maximum(local_var, 0.0)

    denominator = np.sqrt(sum_w0_sq * local_var)
    gamma = np.where(denominator > eps, numerator / denominator, 0.0)
    return np.clip(gamma, -1.0, 1.0)


def normalized_cross_correlation_direct(image, template):
    # Slow textbook double-loop version, kept as a reference / correctness check.
    image = image.astype(np.float64)
    template = template.astype(np.float64)
    th, tw = template.shape
    h, w = image.shape
    w_bar = template.mean()
    w0 = template - w_bar
    sum_w0_sq = (w0 ** 2).sum()

    out = np.zeros((h - th + 1, w - tw + 1))
    for y in range(h - th + 1):
        for x in range(w - tw + 1):
            window = image[y:y + th, x:x + tw]
            f0 = window - window.mean()
            denom = np.sqrt(sum_w0_sq * (f0 ** 2).sum())
            if denom > 1e-7:
                out[y, x] = (w0 * f0).sum() / denom
    return np.clip(out, -1.0, 1.0)
