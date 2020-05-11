from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pyssht as ssht
from scipy import io as sio

from pys2sleplet.flm.functions import Functions


@dataclass
class Earth(Functions):
    L: int

    def __post_init__(self) -> None:
        super().__post_init__()
        self.reality = True

    @staticmethod
    def _load_flm() -> np.ndarray:
        """
        load coefficients from file
        """
        matfile = str(
            Path(__file__).resolve().parents[2]
            / "data"
            / "maps"
            / "earth"
            / "EGM2008_Topography_flms_L2190.mat"
        )
        mat_contents = sio.loadmat(matfile)
        flm = np.ascontiguousarray(mat_contents["flm"][:, 0])
        return flm

    def _setup_args(self, args: Optional[List[int]]) -> None:
        pass

    def _create_flm(self, L: int) -> np.ndarray:
        # load in data
        flm = self._load_flm()

        # fill in negative m components so as to
        # avoid confusion with zero values
        for ell in range(1, L):
            for m in range(1, ell + 1):
                ind_pm = ssht.elm2ind(ell, m)
                ind_nm = ssht.elm2ind(ell, -m)
                flm[ind_nm] = (-1) ** m * flm[ind_pm].conj()

        # don't take the full L
        # invert dataset as Earth backwards
        flm = flm[: L * L].conj()
        return flm

    def _create_name(self) -> str:
        name = "earth"
        return name

    def _create_annotations(self) -> List[Dict]:
        pass
