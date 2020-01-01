from pathlib import Path

import numpy as np
import pyssht as ssht
from scipy import io as sio

from ..functions import Functions


class WMAP(Functions):
    def __init__(self, L: int):
        name = "wmap"
        self.reality = True
        super().__init__(name, L)

    @staticmethod
    def load_cl():
        # pick model
        # file_ending = '_lcdm_pl_model_yr1_v1'
        # file_ending = '_tt_spectrum_7yr_v4p1'
        file_ending = "_lcdm_pl_model_wmap7baoh0"

        matfile = str(
            Path(__file__).resolve().parents[2]
            / "data"
            / "maps"
            / "wmap"
            / f"wmap{file_ending}"
        )
        mat_contents = sio.loadmat(matfile)
        cl = np.ascontiguousarray(mat_contents["cl"][:, 0])
        return cl

    def _create_flm(self) -> np.ndarray:
        # load in data
        cl = self.load_cl()

        # same random seed
        np.random.seed(0)

        # Simulate CMB in harmonic space.
        flm = np.zeros((self.L * self.L), dtype=complex)
        for ell in range(2, self.L):
            cl[ell - 1] = cl[ell - 1] * 2 * np.pi / (ell * (ell + 1))
            for m in range(-ell, ell + 1):
                ind = ssht.elm2ind(ell, m)
                if m == 0:
                    flm[ind] = np.sqrt(cl[ell - 1]) * np.random.randn()
                else:
                    flm[ind] = (
                        np.sqrt(cl[ell - 1] / 2) * np.random.randn()
                        + 1j * np.sqrt(cl[ell - 1] / 2) * np.random.randn()
                    )
        return flm