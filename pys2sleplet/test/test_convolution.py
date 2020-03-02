import numpy as np

from pys2sleplet.flm.kernels.harmonic_gaussian import HarmonicGaussian
from pys2sleplet.flm.kernels.identity import Identity
from pys2sleplet.flm.maps.earth import Earth
from pys2sleplet.plotting.create_plot import Plot
from pys2sleplet.utils.config import config
from pys2sleplet.utils.logger import logger


def test_earth_identity_convolution() -> None:
    """
    test to ensure that the convolving with the
    identity function doesn't change the map
    """
    # setup
    f = Earth(config.L)
    g = Identity(config.L)
    flm = f.multipole

    # convolution
    f.convolve(g.multipole)
    flm_conv = f.multipole

    # perform test
    np.testing.assert_equal(flm, flm_conv)
    logger.info("Identity convolution passed test")


def test_earth_harmonic_gaussian_convolution() -> None:
    """
    test to ensure that convolving the Earth with the harmonic
    Gausian does not change significantly change the map
    """
    # setup
    f = Earth(config.L)
    g = HarmonicGaussian(config.L)
    flm = f.multipole
    f_map = f.field

    # convolution
    f.convolve(g.multipole)
    flm_conv = f.multipole
    f_conv = f.field

    # calculate difference
    flm_diff = flm - flm_conv
    f_diff = f_map - f_conv

    # perform test
    np.testing.assert_allclose(flm, flm_conv, atol=5e1)
    np.testing.assert_allclose(f_map, f_conv, atol=8e2)
    logger.info(
        "Earth/harmonic gaussian convolution difference max error:",
        np.max(np.abs(flm_diff)),
    )

    if config.AUTO_OPEN:
        filename = f"{g.name}_L{config.L}_diff_{f.name}_res{f.resolution}_real"
        Plot(f_diff.real, f.resolution, filename).execute()
