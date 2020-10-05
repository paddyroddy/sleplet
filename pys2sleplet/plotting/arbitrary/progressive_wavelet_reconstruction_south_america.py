from pys2sleplet.flm.kernels.slepian_wavelets import SlepianWavelets
from pys2sleplet.flm.maps.south_america import SouthAmerica
from pys2sleplet.plotting.create_plot import Plot
from pys2sleplet.utils.plot_methods import calc_plot_resolution
from pys2sleplet.utils.region import Region
from pys2sleplet.utils.slepian_methods import slepian_forward, slepian_inverse
from pys2sleplet.utils.wavelet_methods import (
    slepian_wavelet_forward,
    slepian_wavelet_inverse,
)
from pys2sleplet.utils.logger import logger
import numpy as np

L = 128


def main() -> None:
    """
    the reconstruction of a signal in Slepian space
    """
    region = Region(mask_name="south_america")
    south_america = SouthAmerica(L, region=region)
    sw = SlepianWavelets(L, region=region)
    coefficients = slepian_forward(L, south_america.multipole, sw.slepian)
    wav_coeffs = slepian_wavelet_forward(coefficients, sw.wavelets)

    # plot
    f_p = np.zeros(L ** 2, dtype=np.complex128)
    for p, coeff in enumerate(wav_coeffs):
        logger.info(f"plot reconstruction: {p}")
        f_p += slepian_wavelet_inverse(coeff, sw.wavelets)
        f = slepian_inverse(L, f_p, sw.slepian)
        resolution = calc_plot_resolution(L)
        name = (
            f"south_america_wavelet_reconstruction_progressive_{p}_L{L}_res{resolution}"
        )
        Plot(f, L, resolution, name).execute()


if __name__ == "__main__":
    main()