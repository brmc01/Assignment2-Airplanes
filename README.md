# Where are the Airplanes?

Assignment 2 (Image Processing, Prof. Zaghetto, UnB). It (1) adds **gaussian
noise** to the airport image and **blurs it back off**, then (2) **finds the
parked planes** with a hand-written normalized cross-correlation template matcher.

The whole thing is three Python files.

## What it does

**Section 1 — denoising.** Gaussian noise is added to the brightness (Y) channel,
then a hand-written gaussian blur averages it away. (Only the FFT, used later in
the matcher, is a library call — everything else is from scratch.)

**Section 2 — finding the planes.** Cut one plane out of the image as a template,
rotate it from −45° to +45° in 9° steps, score every rotation against the image
with normalized cross-correlation (Gonzalez & Woods eq. 12.2-8), keep the best
matches, and circle them.

It produces **four pictures**: the noisy image, the denoised image, the template
used, and the planes highlighted (plus a `summary.png` with all four side by side).

## Files

```
main.py          runs everything + small image/colour helpers + the template box
denoising.py     Section 1: gaussian noise + the hand-written blur
detection.py     Section 2: cross-correlation + rotate/match/dedupe/draw
make_docs.py     builds Documentation.pdf
images/          the source airport image
output/          generated results (made on first run)
RUN_ME.bat       double-click launcher
```

## How to run

**Easiest:** double-click `RUN_ME.bat`. First run sets up the environment
(~1 min); after that it's instant.

**In VSCode:** open this folder and press **F5**, or just hit the Run button on
`main.py` — it re-launches itself with the project's Python automatically, so it
works even if VSCode has a different interpreter selected.

**In a terminal:**
```powershell
./venv/Scripts/python.exe main.py            # run + show window + open folder
./venv/Scripts/python.exe main.py --no-show  # just write the files
```

## Output

Everything lands in `output/`: `01_noisy`, `02_denoised`, `03_template`,
`04_detections`, and `summary.png`. The terminal also prints the PSNR and each
plane's location/score/angle.

## Tweaking

The numbers to change are the constants at the top of `denoising.py`
(`GAUSS_SIGMA`, `GAUSS_SIZE`) and `detection.py` (`THRESHOLD`, `MIN_GAP`,
rotation range), plus `TEMPLATE_BOX` in `main.py`. The most useful is `THRESHOLD`:
higher → fewer, surer hits; lower → more hits but more false alarms.
