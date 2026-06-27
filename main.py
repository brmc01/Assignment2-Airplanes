import argparse
import os
import subprocess
import sys

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


def open_in_explorer(path):
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.run(["open", path], check=False)
        else:
            subprocess.run(["xdg-open", path], check=False)
    except Exception:
        pass


def main(show=True, open_output=True):
    out = config.OUTPUT_DIR
    print("=" * 70)
    print("Assignment 2: Where are the Airplanes?")
    print("=" * 70)

    # Load the clean base image.
    clean_rgb = iu.load_rgb(config.SOURCE_IMAGE)
    clean_ycbcr = iu.rgb_to_ycbcr(clean_rgb)
    iu.save_rgb(os.path.join(out, "01_clean.png"), clean_rgb)
    print(f"[load] clean image {clean_rgb.shape} from {os.path.basename(config.SOURCE_IMAGE)}")

    # Section 1: add noise, then denoise.
    print("\n[Section 1] Image denoising")
    noisy_ycbcr = Noise.make_noisy(clean_ycbcr, seed=config.RANDOM_SEED)
    noisy_rgb = iu.ycbcr_to_rgb(noisy_ycbcr)
    iu.save_rgb(os.path.join(out, "02_noisy.png"), noisy_rgb)
    print(f"  added: Gaussian(Y, sigma={config.GAUSSIAN_SIGMA}), "
          f"salt&pepper(Cb, {config.SALT_PEPPER_AMOUNT}), "
          f"periodic(Cr, period={config.PERIODIC_PERIOD})")

    denoised_ycbcr, spec_before, spec_after, peaks = denoise.denoise_ycbcr(
        noisy_ycbcr, collect_spectrum=True)
    denoised_rgb = iu.ycbcr_to_rgb(denoised_ycbcr)
    iu.save_rgb(os.path.join(out, "03_denoised.png"), denoised_rgb)
    print(f"  Y  -> Gaussian low-pass {config.GAUSSIAN_FILTER_SIZE}x{config.GAUSSIAN_FILTER_SIZE}")
    print(f"  Cb -> median filter {config.MEDIAN_FILTER_SIZE}x{config.MEDIAN_FILTER_SIZE}")
    print(f"  Cr -> notch reject at spectral peaks {peaks}")
    print(f"  PSNR noisy vs clean   : {psnr(clean_rgb, noisy_rgb):5.2f} dB")
    print(f"  PSNR denoised vs clean: {psnr(clean_rgb, denoised_rgb):5.2f} dB")

    # Section 2: crop the template and find the airplanes.
    print("\n[Section 2] Finding the airplanes")
    box = config.TEMPLATE_BOX
    template_rgb = denoised_rgb[box[1]:box[3], box[0]:box[2]]
    template_ycbcr = iu.rgb_to_ycbcr(template_rgb)
    iu.save_rgb(os.path.join(out, "04_template.png"), template_rgb)
    n_angles = len(range(config.ROTATION_MIN_DEG,
                         config.ROTATION_MAX_DEG + 1, config.ROTATION_STEP_DEG))
    print(f"  template {template_rgb.shape[:2]} from box {box}")
    print(f"  matching with {n_angles} rotations "
          f"({config.ROTATION_MIN_DEG}..{config.ROTATION_MAX_DEG} deg, "
          f"step {config.ROTATION_STEP_DEG})")

    detections, resp = detect.find_airplanes(denoised_ycbcr, template_ycbcr)
    print(f"  airplanes found: {len(detections)}")
    for i, (score, cy, cx, angle) in enumerate(detections, start=1):
        print(f"    #{i:2d}  (x={cx:3d}, y={cy:3d})  score={score:.3f}  angle={angle:+d} deg")

    resp_vis = np.clip(resp, 0, 1)
    plt.imsave(os.path.join(out, "05_response.png"), resp_vis, cmap="inferno")

    marked = detect.draw_detections(denoised_rgb, detections, template_box=box)
    marked.save(os.path.join(out, "06_detections.png"))

    _summary_figure(clean_rgb, noisy_rgb, denoised_rgb, template_rgb,
                    spec_before, spec_after, resp_vis, marked,
                    os.path.join(out, "summary.png"), show)

    print("\n" + "=" * 70)
    print("DONE!  Results saved in the 'output' folder:")
    for name in ("01_clean.png", "02_noisy.png", "03_denoised.png",
                 "04_template.png", "05_response.png", "06_detections.png",
                 "summary.png"):
        print(f"   - output/{name}")
    print("=" * 70)
    if open_output:
        open_in_explorer(out)


def _summary_figure(clean, noisy, denoised, template, spec_before, spec_after,
                    resp, marked, path, show):
    fig, ax = plt.subplots(2, 4, figsize=(18, 9))
    u8 = lambda a: np.clip(a, 0, 255).astype(np.uint8)

    ax[0, 0].imshow(u8(clean));    ax[0, 0].set_title("1. Clean (from PDF)")
    ax[0, 1].imshow(u8(noisy));    ax[0, 1].set_title("2. Noisy (Y+Cb+Cr noise)")
    ax[0, 2].imshow(u8(denoised)); ax[0, 2].set_title("3. Denoised")
    ax[0, 3].imshow(u8(template)); ax[0, 3].set_title("4. Airplane template")

    ax[1, 0].imshow(spec_before, cmap="gray")
    ax[1, 0].set_title("Cr spectrum (noisy)")
    ax[1, 1].imshow(spec_after, cmap="gray")
    ax[1, 1].set_title("Cr spectrum (notched)")
    ax[1, 2].imshow(resp, cmap="inferno")
    ax[1, 2].set_title("5. NCC response")
    ax[1, 3].imshow(np.asarray(marked))
    ax[1, 3].set_title("6. Airplanes found")

    for a in ax.ravel():
        a.axis("off")
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    print(f"  summary montage -> {os.path.basename(path)}")
    if show:
        plt.show()
    else:
        plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Assignment 2 - airplane finder")
    parser.add_argument("--no-show", action="store_true",
                        help="don't pop up the results window (just write files)")
    parser.add_argument("--no-open", action="store_true",
                        help="don't open the output folder when finished")
    args = parser.parse_args()
    show = not args.no_show
    if not show:
        matplotlib.use("Agg")
    main(show=show, open_output=not args.no_open)
