
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