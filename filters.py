"""
Section 1, part B: the filters.

All filters are written from scratch. Only the FFT (numpy.fft) is used, which is
the one built-in the assignment allows.
"""

import numpy as np

import config


def pad_reflect(channel, pad):
    return np.pad(channel, pad, mode="reflect")


def convolve2d(channel, kernel):
    # Shift-and-accumulate convolution: for each kernel weight, add the shifted
    # (padded) image scaled by that weight.
    kh, kw = kernel.shape
    assert kh % 2 == 1 and kw % 2 == 1, "kernel dimensions must be odd"
    py, px = kh // 2, kw // 2
    padded = pad_reflect(channel, max(py, px))
    h, w = channel.shape

    out = np.zeros_like(channel, dtype=np.float64)
    for i in range(kh):
        for j in range(kw):
            weight = kernel[kh - 1 - i, kw - 1 - j]   # flipped: convolution
            if weight == 0.0:
                continue
            ys = max(py, px) - py + i
            xs = max(py, px) - px + j
            out += weight * padded[ys:ys + h, xs:xs + w]
    return out


def gaussian_kernel(size, sigma):
    ax = np.arange(size) - (size - 1) / 2.0
    xx, yy = np.meshgrid(ax, ax)
    k = np.exp(-(xx ** 2 + yy ** 2) / (2.0 * sigma ** 2))
    return k / k.sum()


def gaussian_smooth(channel, size=None, sigma=None):
    # Low-pass blur for the Gaussian-corrupted Y channel.
    size = size or config.GAUSSIAN_FILTER_SIZE
    sigma = sigma or config.GAUSSIAN_FILTER_SIGMA
    return convolve2d(channel, gaussian_kernel(size, sigma))


def median_filter(channel, size=None):
    # Per-pixel median over the neighbourhood; removes salt & pepper outliers.
    size = size or config.MEDIAN_FILTER_SIZE
    assert size % 2 == 1, "median window must be odd"
    pad = size // 2
    padded = pad_reflect(channel, pad)
    h, w = channel.shape

    windows = np.empty((size * size, h, w), dtype=np.float64)
    idx = 0
    for dy in range(size):
        for dx in range(size):
            windows[idx] = padded[dy:dy + h, dx:dx + w]
            idx += 1
    return np.median(windows, axis=0)


def _find_spectral_peaks(magnitude, exclude_radius, num_peaks):
    # Brightest spectrum points away from DC (the periodic-noise spikes).
    h, w = magnitude.shape
    cy, cx = h // 2, w // 2
    yy, xx = np.mgrid[0:h, 0:w]
    dist = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)

    work = magnitude.copy()
    work[dist < exclude_radius] = 0.0

    peaks = []
    for _ in range(num_peaks):
        py, px = np.unravel_index(np.argmax(work), work.shape)
        if work[py, px] <= 0:
            break
        peaks.append((py, px))
        local = np.sqrt((yy - py) ** 2 + (xx - px) ** 2)
        work[local < exclude_radius] = 0.0
    return peaks


def notch_reject_filter(channel, radius=None, exclude_radius=None, num_peaks=None,
                        return_spectrum=False):
    # FFT -> find the noise spikes -> zero them with a smooth notch -> inverse FFT.
    radius = radius or config.NOTCH_RADIUS
    exclude_radius = exclude_radius or config.NOTCH_EXCLUDE_RADIUS
    num_peaks = num_peaks or config.NOTCH_NUM_PEAKS

    f = np.fft.fftshift(np.fft.fft2(channel))
    magnitude = np.abs(f)

    h, w = channel.shape
    yy, xx = np.mgrid[0:h, 0:w]
    peaks = _find_spectral_peaks(magnitude, exclude_radius, num_peaks)

    notch = np.ones((h, w), dtype=np.float64)
    for (py, px) in peaks:
        d = np.sqrt((yy - py) ** 2 + (xx - px) ** 2)
        notch *= (1.0 - np.exp(-(d ** 2) / (2.0 * radius ** 2)))

    f_filtered = f * notch
    result = np.real(np.fft.ifft2(np.fft.ifftshift(f_filtered)))

    if return_spectrum:
        spectrum_before = np.log1p(magnitude)
        spectrum_after = np.log1p(np.abs(f_filtered))
        return result, spectrum_before, spectrum_after, peaks
    return result
