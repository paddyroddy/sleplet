from typing import List

import numpy as np

from pys2sleplet.utils.plot_methods import ensure_f_bandlimited
from pys2sleplet.utils.string_methods import filename_args, verify_args

from ..functions import Functions


class SquashedGaussian(Functions):
    def __init__(self, L: int, args: List[int] = None):
        self.reality = True
        if args is not None:
            verify_args(args, 2)
            self.__t_sigma, self.__freq = [10 ** x for x in args]
        else:
            self.__t_sigma, self.__freq = 1e-2, 1e-1
        super().__init__(L, args)

    def _create_flm(self, L: int) -> np.ndarray:
        flm = ensure_f_bandlimited(self._grid_fun, L, self.reality)
        return flm

    def _create_name(self) -> str:
        name = f"squashed_gaussian{filename_args(self.t_sigma, 'tsig')}{filename_args(self.freq, 'freq')}"
        return name

    @property
    def t_sigma(self) -> float:
        return self.__t_sigma

    @t_sigma.setter
    def t_sigma(self, var: int) -> None:
        self.__t_sigma = 10 ** var

    @property
    def freq(self) -> float:
        return self.__freq

    @freq.setter
    def freq(self, var: int) -> None:
        self.__freq = 10 ** var

    def _grid_fun(
        self, theta: np.ndarray, phi: np.ndarray, theta_0: float = 0
    ) -> np.ndarray:
        """
        function on the grid
        """
        f = np.exp(-(((theta - theta_0) / self.t_sigma) ** 2) / 2) * np.sin(
            self.freq * phi
        )
        return f
