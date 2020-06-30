import numpy as np
import pytest
from numpy.testing import assert_allclose

from pys2sleplet.slepian.slepian_region.slepian_arbitrary import SlepianArbitrary
from pys2sleplet.test.constants import L_SMALL as L


def test_equality_to_polar_cap_method(slepian_polar_cap) -> None:
    """
    tests that the eigenvectors and eigenvalues are close
    in comparison to the smarter Slepian polar cap method
    """
    pass


@pytest.mark.slow
def test_equality_to_lim_lat_lon_method(slepian_lim_lat_lon) -> None:
    """
    tests that the eigenvectors and eigenvalues are close
    in comparison to the smarter Slepian lim lat lon method
    """
    mask_name = slepian_lim_lat_lon.region.name_ending
    slepian = SlepianArbitrary(L, mask_name)
    assert_allclose(
        np.abs(slepian.eigenvalues - slepian_lim_lat_lon.eigenvalues).mean(),
        0,
        atol=1e-3,
    )
    assert_allclose(
        np.abs(slepian.eigenvectors - slepian_lim_lat_lon.eigenvectors).mean(),
        0,
        atol=0.09,
    )
