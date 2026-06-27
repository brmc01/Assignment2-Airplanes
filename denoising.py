# Section 1 - add the three kinds of noise the assignment describes, then clean
# them off again. All the filtering is done by hand; the only library shortcut is
# the FFT (which the assignment says we're allowed to use).

import numpy as np

# noise we add to the clean image (so there's something to fix)
GAUSS_SIGMA = 18.0     # brightness fuzz on Y
SP_AMOUNT = 0.06       # salt & pepper on Cb
WAVE_AMP = 28.0        # stripe pattern on Cr
WAVE_PERIOD = 7
WAVE_ANGLE = 35.0

# filter settings
GAUSS_SIZE = 5
GAUSS_KSIGMA = 1.2
MEDIAN_SIZE = 3
NOTCH_RADIUS = 9
NOTCH_KEEP = 22        # leave the bright centre of the spectrum alone
NOTCH_PEAKS = 4


def add_noise(ycbcr, seed=42):
    rng = np.random.default_rng(seed)
    y, cb, cr = ycbcr[..., 0], ycbcr[..., 1].copy(), ycbcr[..., 2]

    # Y: gaussian fuzz
    y = y + rng.normal(0, GAUSS_SIGMA, y.shape)

    # Cb: salt & pepper - slam some pixels to black or white
    pick = rng.random(cb.shape)
    cb[pick < SP_AMOUNT / 2] = 0
    cb[pick > 1 - SP_AMOUNT / 2] = 255

    # Cr: a diagonal wave laid over the channel
    h, w = cr.shape
    yy, xx = np.mgrid[0:h, 0:w]
    ang = np.deg2rad(WAVE_ANGLE)
    cr = cr + WAVE_AMP * np.sin(2 * np.pi * (xx * np.cos(ang) + yy * np.sin(ang)) / WAVE_PERIOD)

    return np.stack([y, cb, cr], -1)


def convolve(channel, kernel):
    # plain 2D convolution: reflect-pad the edges, then for each kernel weight add
    # a shifted copy of the image. kernel is square and odd-sized.
    k = kernel.shape[0]
    pad = k // 2
    p = np.pad(channel, pad, mode="reflect")
    h, w = channel.shape
    out = np.zeros((h, w))
    for i in range(k):
        for j in range(k):
            out += kernel[k - 1 - i, k - 1 - j] * p[i:i + h, j:j + w]   # flip = convolution
    return out


def gaussian_kernel(size, sigma):
    ax = np.arange(size) - (size - 1) / 2
    xx, yy = np.meshgrid(ax, ax)
    k = np.exp(-(xx ** 2 + yy ** 2) / (2 * sigma ** 2))
    return k / k.sum()


def blur(channel):
    # gaussian fuzz -> soft blur averages it away
    return convolve(channel, gaussian_kernel(GAUSS_SIZE, GAUSS_KSIGMA))


def median(channel, size=MEDIAN_SIZE):
    # salt & pepper -> the median of each little window ignores the black/white spikes
    pad = size // 2
    p = np.pad(channel, pad, mode="reflect")
    h, w = channel.shape
    stack = [p[dy:dy + h, dx:dx + w] for dy in range(size) for dx in range(size)]
    return np.median(stack, axis=0)


def notch(channel, want_spectrum=False):
    # the stripe noise shows up as a few bright spikes in the FFT. find them, zero
    # them out, and transform back.
    F = np.fft.fftshift(np.fft.fft2(channel))
    mag = np.abs(F)
    h, w = channel.shape
    cy, cx = h // 2, w // 2
    yy, xx = np.mgrid[0:h, 0:w]

    # don't touch the bright centre - that's the real image, not noise
    work = mag.copy()
    work[np.hypot(yy - cy, xx - cx) < NOTCH_KEEP] = 0

    peaks = []
    for _ in range(NOTCH_PEAKS):
        py, px = np.unravel_index(np.argmax(work), work.shape)
        if work[py, px] <= 0:
            break
        peaks.append((py, px))
        work[np.hypot(yy - py, xx - px) < NOTCH_KEEP] = 0   # so the next argmax finds a new spike

    # mask that dips to zero around each spike (and its mirror, by symmetry)
    mask = np.ones((h, w))
    for py, px in peaks:
        mask *= 1 - np.exp(-(np.hypot(yy - py, xx - px) ** 2) / (2 * NOTCH_RADIUS ** 2))

    cleaned = np.real(np.fft.ifft2(np.fft.ifftshift(F * mask)))
    if want_spectrum:
        return cleaned, np.log1p(mag), np.log1p(np.abs(F * mask)), peaks
    return cleaned


def denoise(noisy, want_spectrum=False):
    # one filter per channel, then stack them back into one image
    y, cb, cr = noisy[..., 0], noisy[..., 1], noisy[..., 2]
    y = blur(y)
    cb = median(cb)
    if want_spectrum:
        cr, before, after, peaks = notch(cr, want_spectrum=True)
        return np.stack([y, cb, cr], -1), before, after, peaks
    cr = notch(cr)
    return np.stack([y, cb, cr], -1)
