from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np

from pys2sleplet.flm.functions import Functions


@dataclass
class Identity(Functions):
    L: int

    def __post_init__(self) -> None:
        super().__post_init__()
        self.reality = True

    def _setup_args(self, args: Optional[List[int]]) -> None:
        pass

    def _create_flm(self, L: int) -> np.ndarray:
        flm = np.ones((L * L)) + 1j * np.zeros((L * L))
        return flm

    def _create_name(self) -> str:
        name = "identity"
        return name

    def _create_annotations(self) -> List[Dict]:
        pass
