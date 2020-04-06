from abc import abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np


@dataclass  # type: ignore
class SlepianFunctions:
    __L: int
    name: str
    __annotations: List[Dict]
    __matrix_location: Path
    __eigenvalues: np.ndarray
    __eigenvectors: np.ndarray

    def __post_init__(self) -> None:
        self.name = self._create_fn_name()
        self.annotations = self._create_annotations()
        self.matrix_location = self._create_matrix_location()
        self.eigenvalues, self.eigenvectors = self._solve_eigenproblem()

    @property
    def L(self) -> int:
        return self.__L

    @L.setter
    def L(self, var: int) -> None:
        self.__L = var

    @property
    def matrix_location(self) -> Path:
        return self.__matrix_location

    @matrix_location.setter
    def matrix_location(self, var: Path) -> None:
        self.__matrix_location = var

    @property
    def annotations(self) -> List[Dict]:
        return self.__annotations

    @annotations.setter
    def annotations(self, var: np.ndarray) -> None:
        self.__annotations = var

    @property
    def eigenvectors(self) -> np.ndarray:
        return self.__eigenvectors

    @eigenvectors.setter
    def eigenvectors(self, var: np.ndarray) -> None:
        self.__eigenvectors = var

    @property
    def eigenvalues(self) -> np.ndarray:
        return self.__eigenvalues

    @eigenvalues.setter
    def eigenvalues(self, var: np.ndarray) -> None:
        self.__eigenvalues = var

    @abstractmethod
    def _create_annotations(self) -> List[Dict]:
        """
        creates the annotations for the plot
        """
        raise NotImplementedError

    @abstractmethod
    def _create_fn_name(self) -> str:
        """
        creates the name for plotting
        """
        raise NotImplementedError

    @abstractmethod
    def _create_matrix_location(self) -> Path:
        """
        creates the name of the matrix binary
        """
        raise NotImplementedError

    @abstractmethod
    def _solve_eigenproblem(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        solves the eigenproblem for the given function
        """
        raise NotImplementedError
