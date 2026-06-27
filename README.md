# Assignment 2 — Where are the Airplanes?

Image-processing pipeline for the UnB assignment *"Where are the Airplanes?"*
(Prof. Alexandre Zaghetto). It (1) **denoises** a corrupted satellite image of the
Dallas/Fort Worth International Airport and (2) **locates the parked airplanes**
with a hand-written **normalized cross-correlation** template matcher.

A full written walk-through of every folder and source file is in
**`Documentation.pdf`**.

---

## What it does

### Section 1 — Image denoising
The assignment states the three YCbCr channels are corrupted by three different
noise types. The PDF only ships an *illustrative* noisy figure (not the real
noisy data), so the pipeline reproduces those exact corruptions on the clean
image and then removes them — making the denoising genuinely demonstrable:

| Channel | Noise | Filter (implemented from scratch) |
|---------|-------|-----------------------------------|
| **Y** (luminance)   | Gaussian        | spatial Gaussian low-pass convolution |
| **Cb** (chrominance)| salt & pepper   | median filter |
| **Cr** (chrominance)| periodic/texture| frequency-domain **notch reject** (uses the FFT) |

Per the assignment, *no built-in filtering functions are used* — only the FFT,
the one explicitly allowed exception (`numpy.fft`).

### Section 2 — Finding the airplanes
1. A template is **manually defined** by cropping one airplane from the denoised
   image (`config.TEMPLATE_BOX`).
2. The template is rotated from **−45° to +45° in 9° steps** (11 orientations;
   built-in rotation is allowed).
3. Each orientation is scored against the image with our own implementation of
   the normalized cross-correlation coefficient (Gonzalez & Woods eq. 12.2-8),
   combining the Y, Cb and Cr channels.
4. The best response per location is thresholded and passed through
   non-maximum suppression to report one point per airplane.

---

## Project layout

```
Assignment2-Airplanes-main/
├── config.py            # all tunable parameters live here
├── imageutils.py        # load/save + manual RGB <-> YCbCr conversion
├── Noise.py             # adds the 3 noise types (builds the noisy input)
├── filters.py           # hand-written convolution, gaussian, median, FFT notch
├── denoise.py           # Section 1 pipeline
├── ncc.py               # hand-written normalized cross-correlation
├── detect.py            # Section 2: rotations, matching, NMS, drawing
├── main.py              # runs everything, writes ./output
├── requirements.txt     # Python dependencies
├── Documentation.pdf    # full explanation of every folder / source file
├── images/              # source airport image (extracted from the PDF)
└── output/              # generated results (created on run)
```

---

## How to run

### Easiest — just double-click
Double-click **`RUN_ME.bat`**. The first time it builds the environment
automatically (~1 min); every run after that is instant. A results window pops
up and the `output` folder opens with all the images.

### In VSCode (one button)
1. Open this folder in VSCode (**File → Open Folder…**).
2. If asked, install the **Python** extension.
3. Press **F5** (or the green ▶ in *Run and Debug*) and pick
   **"▶ Run Assignment (show results)"**.

The terminal prints progress, a window pops up with every stage, and the
`output` folder opens automatically.

> The Python interpreter is pre-pointed at `./venv/Scripts/python.exe`
> (see `.vscode/settings.json`), so you don't have to choose it.

### In a terminal
```powershell
./venv/Scripts/python.exe main.py            # run + show window + open folder
./venv/Scripts/python.exe main.py --no-show  # just write files, no popups
```

### Rebuilding the environment from scratch (only if needed)
```powershell
python -m venv venv
./venv/Scripts/python.exe -m pip install -r requirements.txt
```

---

## Outputs (written to `./output`)

| File | Meaning |
|------|---------|
| `01_clean.png`      | base airport image (extracted from the PDF) |
| `02_noisy.png`      | after Gaussian + salt&pepper + periodic noise |
| `03_denoised.png`   | **Section 1 result** — the single denoised image |
| `04_template.png`   | the manually defined airplane template |
| `05_response.png`   | normalized-cross-correlation response heatmap |
| `06_detections.png` | **Section 2 result** — airplane locations marked |
| `summary.png`       | montage of every stage (incl. the Cr spectrum before/after notch) |

The console also prints the PSNR improvement from denoising and the
`(x, y)` coordinate, score and best-matching angle of every detected airplane.

---

## Tuning

Everything lives in `config.py`. The most useful knob is `NCC_THRESHOLD`:

* **higher** (e.g. `0.5`) → fewer, very confident detections, no false positives;
* **lower** (e.g. `0.40`) → catches more of the faint/rotated planes, but the
  bright terminal roofs start to false-match.

You can also change the template (`TEMPLATE_BOX`), the rotation range/step, the
noise levels, and each filter's window size.
