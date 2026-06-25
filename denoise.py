
import numpy as np

import filters


def denoise_ycbcr(noisy_ycbcr, collect_spectrum=False):

    y, cb, cr = (noisy_ycbcr[..., 0], noisy_ycbcr[..., 1], noisy_ycbcr[..., 2])

    y_d = filters.gaussian_smooth(y)
    cb_d = filters.median_filter(cb)

    if collect_spectrum:
        cr_d, spec_before, spec_after, peaks = filters.notch_reject_filter(
            cr, return_spectrum=True)
    else:
        cr_d = filters.notch_reject_filter(cr)

    denoised = np.stack([y_d, cb_d, cr_d], axis=-1)

    if collect_spectrum:
        return denoised, spec_before, spec_after, peaks
    return denoised

