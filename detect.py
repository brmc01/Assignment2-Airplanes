"""Section 2: rotate the template, match it, drop duplicates, draw the result."""

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import config
from ncc import normalized_cross_correlation


def _rotate_channel(channel, angle, fill):
    img = Image.fromarray(channel.astype(np.float32), mode="F")
    rot = img.rotate(angle, resample=Image.BILINEAR, expand=True, fillcolor=fill)
    return np.asarray(rot, dtype=np.float64)


def build_rotated_templates(template_ycbcr):
    # One template per rotation angle. The mask marks real pixels vs the blank
    # corners that rotation adds, so the corners are ignored when scoring.
    angles = range(config.ROTATION_MIN_DEG,
                   config.ROTATION_MAX_DEG + 1,
                   config.ROTATION_STEP_DEG)
    ones = np.ones(template_ycbcr.shape[:2], dtype=np.float64)

    templates = []
    for angle in angles:
        chans = [_rotate_channel(template_ycbcr[..., c], angle,
                                 float(template_ycbcr[..., c].mean()))
                 for c in range(3)]
        mask = (_rotate_channel(ones, angle, 0.0) > 0.5).astype(np.float64)
        templates.append((angle, chans, mask))
    return templates


def response_map(image_ycbcr, templates):
    # Best score per pixel, plus the list of above-threshold candidates.
    h, w = image_ycbcr.shape[:2]
    best = np.full((h, w), -1.0, dtype=np.float64)
    candidates = []

    img_chans = [image_ycbcr[..., c] for c in range(3)]

    for angle, chans, mask in templates:
        th, tw = mask.shape
        gamma = np.zeros((h - th + 1, w - tw + 1), dtype=np.float64)
        for c in range(3):
            gamma += config.CHANNEL_WEIGHTS[c] * normalized_cross_correlation(
                img_chans[c], chans[c], mask=mask)

        # Move scores from the top-left anchor to the window centre.
        oy, ox = th // 2, tw // 2
        gh, gw = gamma.shape
        region = best[oy:oy + gh, ox:ox + gw]
        np.maximum(region, gamma, out=region)

        ys, xs = np.where(gamma >= config.NCC_THRESHOLD)
        for y, x in zip(ys, xs):
            candidates.append((gamma[y, x], y + oy, x + ox, angle))

    return best, candidates


def non_max_suppression(candidates, min_distance, max_detections):
    # Keep the highest scores, drop any hit too close to a stronger one.
    candidates = sorted(candidates, key=lambda c: c[0], reverse=True)
    kept = []
    for score, cy, cx, angle in candidates:
        if all((cy - ky) ** 2 + (cx - kx) ** 2 >= min_distance ** 2
               for _, ky, kx, _ in kept):
            kept.append((score, cy, cx, angle))
        if len(kept) >= max_detections:
            break
    return kept


def find_airplanes(image_ycbcr, template_ycbcr):
    templates = build_rotated_templates(template_ycbcr)
    resp, candidates = response_map(image_ycbcr, templates)
    detections = non_max_suppression(candidates,
                                     config.NMS_MIN_DISTANCE,
                                     config.MAX_DETECTIONS)
    return detections, resp


def draw_detections(rgb, detections, template_box=None, radius=18):
    img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), mode="RGB")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except Exception:
        font = ImageFont.load_default()

    if template_box is not None:
        draw.rectangle(template_box, outline=(0, 255, 255), width=2)
        draw.text((template_box[0], template_box[1] - 16), "template",
                  fill=(0, 255, 255), font=font)

    for i, (score, cy, cx, angle) in enumerate(detections, start=1):
        draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
                     outline=(255, 0, 0), width=3)
        draw.text((cx + radius + 2, cy - radius), str(i),
                  fill=(255, 255, 0), font=font)
    return img
