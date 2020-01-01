import numpy as np

from ..functions import Functions


class Identity(Functions):
    def __init__(self, L: int):
        name = "identity"
        self.reality = False
        super().__init__(name, L)

    def _create_flm(self) -> np.ndarray:
        flm = np.ones((self.L * self.L)) + 1j * np.zeros((self.L * self.L))
        return flm