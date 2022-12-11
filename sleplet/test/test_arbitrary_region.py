import numpy as np
import pytest
from numpy.testing import assert_allclose

from sleplet.slepian.slepian_region.slepian_arbitrary import SlepianArbitrary


@pytest.mark.slow
def test_equality_to_polar_cap_method(slepian_polar_cap) -> None:
    """
    tests that the eigenvectors and eigenvalues are close
    in comparison to the smarter Slepian polar cap method
    """
    mask_name = slepian_polar_cap.region.name_ending
    slepian = SlepianArbitrary(slepian_polar_cap.L, mask_name)
    assert_allclose(np.abs(slepian_polar_cap.N - slepian.N), 0, atol=3)
    assert_allclose(
        np.abs(
            slepian.eigenvalues[: slepian_polar_cap.N]
            - slepian_polar_cap.eigenvalues[: slepian_polar_cap.N]
        ).mean(),
        0,
        atol=0.05,
    )
    assert_allclose(
        np.abs(
            slepian.eigenvectors[: slepian_polar_cap.N]
            - slepian_polar_cap.eigenvectors[: slepian_polar_cap.N]
        ).mean(),
        0,
        atol=0.03,
    )


@pytest.mark.slow
def test_equality_to_lim_lat_lon_method(slepian_lim_lat_lon) -> None:
    """
    tests that the eigenvectors and eigenvalues are close
    in comparison to the smarter Slepian lim lat lon method
    """
    mask_name = slepian_lim_lat_lon.region.name_ending
    slepian = SlepianArbitrary(slepian_lim_lat_lon.L, mask_name)
    assert_allclose(np.abs(slepian_lim_lat_lon.N - slepian.N), 0, atol=1)
    assert_allclose(
        np.abs(
            slepian.eigenvalues[: slepian_lim_lat_lon.N]
            - slepian_lim_lat_lon.eigenvalues[: slepian_lim_lat_lon.N]
        ).mean(),
        0,
        atol=0.05,
    )
    assert_allclose(
        np.abs(slepian.eigenvectors - slepian_lim_lat_lon.eigenvectors)[
            : slepian_lim_lat_lon.N
        ].mean(),
        0,
        atol=0.03,
    )