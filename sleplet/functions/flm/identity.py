from dataclasses import dataclass

import numpy as np

from sleplet.functions.f_lm import F_LM
from sleplet.utils.string_methods import convert_camel_case_to_snake_case


@dataclass
class Identity(F_LM):
    def __post_init__(self) -> None:
        super().__post_init__()

    def _create_coefficients(self) -> None:
        self.coefficients = np.ones(self.L**2, dtype=np.complex_)

    def _create_name(self) -> None:
        self.name = convert_camel_case_to_snake_case(self.__class__.__name__)

    def _set_reality(self) -> None:
        self.reality = True

    def _set_spin(self) -> None:
        self.spin = 0

    def _setup_args(self) -> None:
        if isinstance(self.extra_args, list):
            raise AttributeError(
                f"{self.__class__.__name__} does not support extra arguments"
            )