"""Configuration: all tunable values for the pipeline live here."""

import glob
import os

# Paths
ROOT = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(ROOT, "images")
OUTPUT_DIR = os.path.join(ROOT, "output")

# Clean airport image (Figure 1.1, extracted from the PDF).
SOURCE_NAME = "page2_img0_720x720.png"


def _resolve_source_image():
    primary = os.path.join(IMAGES_DIR, SOURCE_NAME)
    if os.path.exists(primary):
        return primary
    matches = glob.glob(os.path.join(ROOT, "**", SOURCE_NAME), recursive=True)
    if matches:
        return matches[0]
    raise FileNotFoundError(f"Could not find '{SOURCE_NAME}' under {ROOT}.")


SOURCE_IMAGE = _resolve_source_image()
os.makedirs(OUTPUT_DIR, exist_ok=True)

RANDOM_SEED = 42

# Section 1: noise added to each channel to build the noisy test image.
GAUSSIAN_SIGMA = 18.0        # Gaussian noise on Y
SALT_PEPPER_AMOUNT = 0.06    # salt & pepper fraction on Cb
PERIODIC_AMPLITUDE = 28.0    # periodic noise amplitude on Cr
PERIODIC_PERIOD = 7          # period in pixels
PERIODIC_ANGLE_DEG = 35.0    # orientation

# Section 1: filter sizes.
GAUSSIAN_FILTER_SIZE = 5     # smoothing window for Y
GAUSSIAN_FILTER_SIGMA = 1.2
MEDIAN_FILTER_SIZE = 3       # median window for Cb
NOTCH_RADIUS = 9             # notch radius for Cr
NOTCH_EXCLUDE_RADIUS = 22    # protect low frequencies near DC
NOTCH_NUM_PEAKS = 4          # spectral peaks to reject

# Section 2: template + matching.
TEMPLATE_BOX = (35, 538, 110, 628)   # crop (left, top, right, bottom)
ROTATION_MIN_DEG = -45
ROTATION_MAX_DEG = 45
ROTATION_STEP_DEG = 9
NCC_THRESHOLD = 0.46         # minimum match score
NMS_MIN_DISTANCE = 36        # min pixels between two planes
MAX_DETECTIONS = 14
CHANNEL_WEIGHTS = (0.6, 0.2, 0.2)    # weight of Y, Cb, Cr in the score
