import numpy as np
import pys2let as s2let
import pyssht as ssht

from pys2sleplet.utils.convolution_methods import sifting_convolution


def slepian_wavelet_forward(
    f_p: np.ndarray, wavelets: np.ndarray, shannon: int
) -> np.ndarray:
    """
    computes the coefficients of the given tiling function in Slepian space
    """
    return find_non_zero_wavelet_coefficients(
        sifting_convolution(wavelets, f_p, shannon=shannon)
    )


def slepian_wavelet_inverse(
    wav_coeffs: np.ndarray, wavelets: np.ndarray, shannon: int
) -> np.ndarray:
    """
    computes the inverse wavelet transform in Slepian space
    """
    # ensure wavelets are the same shape as the coefficients
    wavelets_shannon = wavelets[: wav_coeffs.shape[0]]
    return sifting_convolution(wavelets_shannon, wav_coeffs.T, shannon=shannon).sum(
        axis=0
    )


def axisymmetric_wavelet_forward(
    L: int, flm: np.ndarray, wavelets: np.ndarray
) -> np.ndarray:
    """
    computes the coefficients of the axisymmetric wavelets
    """
    w = np.zeros(wavelets.shape, dtype=np.complex_)
    for ell in range(L):
        ind_m0 = ssht.elm2ind(ell, 0)
        wav_0 = np.sqrt((4 * np.pi) / (2 * ell + 1)) * wavelets[:, ind_m0].conj()
        for m in range(-ell, ell + 1):
            ind = ssht.elm2ind(ell, m)
            w[:, ind] = wav_0 * flm[ind]
    return w


def axisymmetric_wavelet_inverse(
    L: int, wav_coeffs: np.ndarray, wavelets: np.ndarray
) -> np.ndarray:
    """
    computes the inverse axisymmetric wavelet transform
    """
    flm = np.zeros(L ** 2, dtype=np.complex_)
    for ell in range(L):
        ind_m0 = ssht.elm2ind(ell, 0)
        wav_0 = np.sqrt((4 * np.pi) / (2 * ell + 1)) * wavelets[:, ind_m0]
        for m in range(-ell, ell + 1):
            ind = ssht.elm2ind(ell, m)
            flm[ind] = (wav_coeffs[:, ind] * wav_0).sum()
    return flm


def compute_wavelet_covariance(wavelets: np.ndarray, var_signal: float) -> np.ndarray:
    """
    computes the theoretical covariance of the wavelet coefficients
    """
    covar_w_theory = np.zeros(wavelets.shape[0], dtype=np.complex128)
    for j, wavelet in enumerate(wavelets):
        covar_w_theory[j] = wavelet @ wavelet.T
    return covar_w_theory * var_signal


def create_axisymmetric_wavelets(L: int, B: int, j_min: int) -> np.ndarray:
    """
    computes the axisymmetric wavelets
    """
    kappa0, kappa = s2let.axisym_wav_l(B, L, j_min)
    wavelets = np.zeros((kappa.shape[1] + 1, L ** 2), dtype=np.complex_)
    for ell in range(L):
        factor = np.sqrt((2 * ell + 1) / (4 * np.pi))
        ind = ssht.elm2ind(ell, 0)
        wavelets[0, ind] = factor * kappa0[ell]
        wavelets[1:, ind] = factor * kappa[ell]
    return wavelets


def create_slepian_wavelets(L: int, B: int, j_min: int) -> np.ndarray:
    """
    computes the Slepian wavelets
    """
    kappa0, kappa = s2let.axisym_wav_l(B, L ** 2, j_min)
    return np.concatenate((kappa0[np.newaxis], kappa.T))


def find_non_zero_wavelet_coefficients(wav_coeffs: np.ndarray) -> np.ndarray:
    """
    finds the coefficients within the shannon number to speed up computations
    """
    return wav_coeffs[wav_coeffs.any(axis=1)]
