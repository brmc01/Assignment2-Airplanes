
import argparse
import os

import numpy as np
import matplotlib
import matplotlib.pyplot as plt

import config
import imageutils as iu
import Noise
import denoise
import detect


def psnr(a, b):

    mse = np.mean((a.astype(np.float64) - b.astype(np.float64)) ** 2)
    if mse == 0:
        return float("inf")
    return 10.0 * np.log10(255.0 ** 2 / mse)


def main(show=False):
    out = config.OUTPUT_DIR
    print("=" * 70)
    print("Assignment 2: Where are the Airplanes?")
    print("=" * 70)

    clean_rgb = iu.load_rgb(config.SOURCE_IMAGE)
    clean_ycbcr = iu.rgb_to_ycbcr(clean_rgb)
    iu.save_rgb(os.path.join(out, "01_clean.png"), clean_rgb)
    print(f"[load] clean image {clean_rgb.shape} from {os.path.basename(config.SOURCE_IMAGE)}")


    print("\n[Section 1] Image denoising")
    rng = np.random.default_rng(config.RANDOM_SEED)
