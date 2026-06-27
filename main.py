# Where are the Airplanes?  -  Assignment 2
#
# Run it:
#   python main.py            run, pop up the results, open the output folder
#   python main.py --no-show  just save the images, no windows
#
# What it does: (1) adds the three kinds of noise the assignment describes and
# cleans them back off, then (2) finds the parked planes by template matching.
# Everything lands in the output/ folder.

import os
import sys
import glob
import argparse
import subprocess

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from PIL import Image

import denoising
import detection

HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT = os.path.join(HERE, "output")
os.makedirs(OUTPUT, exist_ok=True)

# the airplane template = this rectangle cut out of the image (left, top, right, bottom)
TEMPLATE_BOX = (35, 538, 110, 628)


def find_image():
    # the airport picture that was pulled out of the assignment PDF
    direct = os.path.join(HERE, "images", "page2_img0_720x720.png")
    if os.path.exists(direct):
        return direct
    hits = glob.glob(os.path.join(HERE, "**", "page2_img0_720x720.png"), recursive=True)
    if not hits:
        raise FileNotFoundError("can't find 'page2_img0_720x720.png'")
    return hits[0]


def load_rgb(path):
    return np.asarray(Image.open(path).convert("RGB"), float)


def save_rgb(path, rgb):
    Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB").save(path)


def rgb_to_ycbcr(rgb):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    y = 0.299 * r + 0.587 * g + 0.114 * b
    cb = 128 - 0.168736 * r - 0.331264 * g + 0.5 * b
    cr = 128 + 0.5 * r - 0.418688 * g - 0.081312 * b
    return np.stack([y, cb, cr], -1)


def ycbcr_to_rgb(ycbcr):
    y = ycbcr[..., 0]
    cb = ycbcr[..., 1] - 128
    cr = ycbcr[..., 2] - 128
    r = y + 1.402 * cr
    g = y - 0.344136 * cb - 0.714136 * cr
    b = y + 1.772 * cb
    return np.stack([r, g, b], -1)


def psnr(a, b):
    mse = np.mean((a.astype(float) - b.astype(float)) ** 2)
    return float("inf") if mse == 0 else 10 * np.log10(255 ** 2 / mse)


def open_folder(path):
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.run(["open", path])
        else:
            subprocess.run(["xdg-open", path])
    except Exception:
        pass


def run(show=True, open_output=True):
    print("Where are the Airplanes?\n")

    clean = load_rgb(find_image())
    save_rgb(os.path.join(OUTPUT, "01_clean.png"), clean)
    clean_ycc = rgb_to_ycbcr(clean)

    # Section 1 - add noise, then take it back off
    print("Section 1 - denoising")
    noisy_ycc = denoising.add_noise(clean_ycc)
    noisy = ycbcr_to_rgb(noisy_ycc)
    save_rgb(os.path.join(OUTPUT, "02_noisy.png"), noisy)

    denoised_ycc, spec_before, spec_after, peaks = denoising.denoise(noisy_ycc, want_spectrum=True)
    denoised = ycbcr_to_rgb(denoised_ycc)
    save_rgb(os.path.join(OUTPUT, "03_denoised.png"), denoised)
    print(f"  PSNR  noisy {psnr(clean, noisy):.1f} dB  ->  denoised {psnr(clean, denoised):.1f} dB")

    # Section 2 - cut out the template and go find the planes
    print("Section 2 - finding planes")
    l, t, r, b = TEMPLATE_BOX
    template = denoised[t:b, l:r]
    save_rgb(os.path.join(OUTPUT, "04_template.png"), template)

    hits, response = detection.find_planes(denoised_ycc, rgb_to_ycbcr(template))
    print(f"  found {len(hits)} planes")
    for i, (score, y, x, angle) in enumerate(hits, 1):
        print(f"    {i:2d}. x={x:3d} y={y:3d}  score={score:.2f}  angle={angle:+d}")

    response = np.clip(response, 0, 1)
    plt.imsave(os.path.join(OUTPUT, "05_response.png"), response, cmap="inferno")
    marked = detection.draw(denoised, hits, box=TEMPLATE_BOX)
    marked.save(os.path.join(OUTPUT, "06_detections.png"))

    summary(clean, noisy, denoised, template, spec_before, spec_after, response, marked, show)
    print(f"\nDone - everything saved in {OUTPUT}")
    if open_output:
        open_folder(OUTPUT)


def summary(clean, noisy, denoised, template, spec_before, spec_after, response, marked, show):
    u8 = lambda a: np.clip(a, 0, 255).astype(np.uint8)
    panels = [
        (u8(clean), "Clean (from PDF)", None),
        (u8(noisy), "Noisy (Y+Cb+Cr noise)", None),
        (u8(denoised), "Denoised", None),
        (u8(template), "Airplane template", None),
        (spec_before, "Cr spectrum (noisy)", "gray"),
        (spec_after, "Cr spectrum (notched)", "gray"),
        (response, "Match response", "inferno"),
        (np.asarray(marked), "Airplanes found", None),
    ]
    fig, ax = plt.subplots(2, 4, figsize=(18, 9))
    for a, (img, title, cmap) in zip(ax.ravel(), panels):
        a.imshow(img, cmap=cmap)
        a.set_title(title)
        a.axis("off")
    fig.tight_layout()
    fig.savefig(os.path.join(OUTPUT, "summary.png"), dpi=110)
    if show:
        plt.show()
    else:
        plt.close(fig)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--no-show", action="store_true", help="don't pop up the window")
    p.add_argument("--no-open", action="store_true", help="don't open the output folder")
    args = p.parse_args()
    if args.no_show:
        matplotlib.use("Agg")
    run(show=not args.no_show, open_output=not args.no_open)
