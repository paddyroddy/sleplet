import numpy as np
from hypothesis import given, settings
from hypothesis.strategies import SearchStrategy, floats
from numpy.testing import assert_allclose

from pys2sleplet.flm.kernels.dirac_delta import DiracDelta
from pys2sleplet.plotting.create_plot import Plot
from pys2sleplet.utils.config import config
from pys2sleplet.utils.logger import logger


def valid_alphas() -> SearchStrategy[float]:
    """
    alpha can be in the range [0, 2*pi)
    """
    return floats(min_value=0, max_value=2, exclude_max=True, width=16)


def valid_betas() -> SearchStrategy[float]:
    """
    beta can be in the range [0, pi]
    """
    return floats(min_value=0, max_value=1, width=16)


@settings(max_examples=8, derandomize=True, deadline=None)
@given(alpha_pi_frac=valid_alphas(), beta_pi_frac=valid_betas())
def test_dirac_delta_rotate_translate(alpha_pi_frac, beta_pi_frac) -> None:
    """
    test to ensure that rotation and translation
    give the same result for the Dirac delta
    """
    dd_1 = DiracDelta(config.L)
    dd_1.rotate(alpha_pi_frac, beta_pi_frac)

    dd_2 = DiracDelta(config.L)
    dd_2.translate(alpha_pi_frac, beta_pi_frac)

    flm_diff = dd_1.multipole - dd_2.multipole
    f_diff = dd_1.field_padded - dd_2.field_padded

    assert_allclose(dd_1.multipole, dd_2.multipole, rtol=1e-13)
    assert_allclose(dd_1.field, dd_2.field, rtol=1e-11)
    logger.info(f"Translation/rotation difference max error: {np.abs(flm_diff).max()}")

    if config.AUTO_OPEN:
        filename = f"{dd_1.name}_L{dd_1.L}_diff_rot_trans_res{dd_1.resolution}"
        Plot(f_diff.real, dd_1.resolution, filename).execute()
