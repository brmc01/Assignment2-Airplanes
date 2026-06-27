"""Section 1, part A: add the three noise types to build the noisy input."""

import numpy as np

import config


def add_gaussian(channel, sigma, rng):
    return channel + rng.normal(0.0, sigma, size=channel.shape)


def add_salt_pepper(channel, amount, rng):
    out = channel.copy()
    mask = rng.random(channel.shape)
    out[mask < amount / 2.0] = 0.0
    out[mask > 1.0 - amount / 2.0] = 255.0
    return out


def add_periodic(channel, amplitude, period, angle_deg):
    # A single 2-D sinusoid; shows up as a pair of spikes in the spectrum.
    h, w = channel.shape
    yy, xx = np.mgrid[0:h, 0:w]
    theta = np.deg2rad(angle_deg)
    proj = xx * np.cos(theta) + yy * np.sin(theta)
    pattern = amplitude * np.sin(2.0 * np.pi * proj / period)
    return channel + pattern


def make_noisy(ycbcr, seed=None):
    if seed is None:
        seed = config.RANDOM_SEED
    rng = np.random.default_rng(seed)
    y, cb, cr = ycbcr[..., 0], ycbcr[..., 1], ycbcr[..., 2]

    y_n = add_gaussian(y, config.GAUSSIAN_SIGMA, rng)
    cb_n = add_salt_pepper(cb, config.SALT_PEPPER_AMOUNT, rng)
    cr_n = add_periodic(cr, config.PERIODIC_AMPLITUDE,
                        config.PERIODIC_PERIOD, config.PERIODIC_ANGLE_DEG)

    return np.stack([y_n, cb_n, cr_n], axis=-1)
