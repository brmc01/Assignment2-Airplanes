# Section 1 - add gaussian noise to the brightness, then blur it back off.
# The blur (convolution) is written by hand.

import numpy as np

GAUSS_SIGMA = 18.0     # how much gaussian noise to add to the Y (brightness) channel
GAUSS_SIZE = 5         # blur window size
GAUSS_KSIGMA = 1.2     # blur strength


def add_noise(ycbcr, seed=42):
    # gaussian fuzz on the brightness channel only
    rng = np.random.default_rng(seed)
    out = ycbcr.copy()
    out[..., 0] = out[..., 0] + rng.normal(0, GAUSS_SIGMA, out[..., 0].shape)
    return out


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
    return convolve(channel, gaussian_kernel(GAUSS_SIZE, GAUSS_KSIGMA))


def denoise(ycbcr):
    # blur the brightness channel to average out the gaussian noise
    out = ycbcr.copy()
    out[..., 0] = blur(out[..., 0])
    return out
