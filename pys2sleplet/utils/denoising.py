from typing import Tuple

import numpy as np
import pyssht as ssht

from pys2sleplet.functions.coefficients import Coefficients
from pys2sleplet.functions.flm.axisymmetric_wavelets import AxisymmetricWavelets
from pys2sleplet.functions.fp.slepian_wavelets import SlepianWavelets
from pys2sleplet.utils.function_dicts import MAPS_LM
from pys2sleplet.utils.logger import logger
from pys2sleplet.utils.noise import (
    compute_sigma_j,
    compute_slepian_sigma_j,
    compute_snr,
    harmonic_hard_thresholding,
    slepian_hard_thresholding,
)
from pys2sleplet.utils.slepian_methods import slepian_inverse
from pys2sleplet.utils.vars import EARTH_ALPHA, EARTH_BETA, EARTH_GAMMA, SAMPLING_SCHEME
from pys2sleplet.utils.wavelet_methods import (
    axisymmetric_wavelet_forward,
    axisymmetric_wavelet_inverse,
    slepian_wavelet_forward,
    slepian_wavelet_inverse,
)


def denoising_axisym(
    name: str, L: int, B: int, j_min: int, n_sigma: int, snr_in: int
) -> Tuple[np.ndarray, float, float]:
    """
    reproduce the denoising demo from s2let paper
    """
    logger.info(f"L={L}, B={B}, J_min={j_min}, n_sigma={n_sigma}, SNR_in={snr_in}")
    # create map & noised map
    fun = MAPS_LM[name](L)
    fun_noised = MAPS_LM[name](L, noise=snr_in)

    # create wavelets
    aw = AxisymmetricWavelets(L, B=B, j_min=j_min)

    # compute wavelet coefficients
    w = axisymmetric_wavelet_forward(L, fun_noised.coefficients, aw.wavelets)

    # compute wavelet noise
    sigma_j = compute_sigma_j(L, fun.coefficients, aw.wavelets[1:], snr_in)

    # hard thresholding
    w_denoised = harmonic_hard_thresholding(L, w, sigma_j, n_sigma)

    # wavelet synthesis
    flm = axisymmetric_wavelet_inverse(L, w_denoised, aw.wavelets)

    # rotate to South America
    flm_rot = (
        ssht.rotate_flms(flm, EARTH_ALPHA, EARTH_BETA, EARTH_GAMMA, L)
        if "earth" in name
        else flm
    )

    # real space
    f = ssht.inverse(flm_rot, L, Method=SAMPLING_SCHEME)

    # compute SNR
    denoised_snr = compute_snr(L, fun.coefficients, flm - fun.coefficients)
    return f, fun_noised.snr, denoised_snr


def denoising_slepian(
    signal: Coefficients,
    noised_signal: Coefficients,
    slepian_wavelets: SlepianWavelets,
    snr_in: int,
    n_sigma: int,
) -> np.ndarray:
    """
    denoising demo using Slepian wavelets
    """
    # compute wavelet coefficients
    w = slepian_wavelet_forward(
        noised_signal.coefficients,
        slepian_wavelets.wavelets,
        slepian_wavelets.slepian.N,
    )

    # compute wavelet noise
    sigma_j = compute_slepian_sigma_j(
        signal.L,
        signal.coefficients,
        slepian_wavelets.wavelets,
        snr_in,
        slepian_wavelets.slepian,
    )

    # hard thresholding
    w_denoised = slepian_hard_thresholding(
        signal.L, w, sigma_j, n_sigma, slepian_wavelets.slepian
    )

    # wavelet synthesis
    f_p = slepian_wavelet_inverse(
        w_denoised, slepian_wavelets.wavelets, slepian_wavelets.slepian.N
    )
    f = slepian_inverse(signal.L, f_p, slepian_wavelets.slepian)

    # compute SNR
    compute_snr(signal.L, signal.coefficients, f_p - signal.coefficients)
    return f
