from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pyssht as ssht
from multiprocess import Pool
from multiprocess.shared_memory import SharedMemory

from pys2sleplet.slepian.slepian_functions import SlepianFunctions
from pys2sleplet.utils.config import settings
from pys2sleplet.utils.integration_methods import integrate_sphere
from pys2sleplet.utils.mask_methods import create_mask_region
from pys2sleplet.utils.parallel_methods import split_L_into_chunks
from pys2sleplet.utils.region import Region

_file_location = Path(__file__).resolve()
_arbitrary_path = _file_location.parents[2] / "data" / "slepian" / "arbitrary"


@dataclass
class SlepianArbitrary(SlepianFunctions):
    mask_name: str
    ncpu: int
    _N: int = field(init=False, repr=False)
    _mask_name: str = field(init=False, repr=False)
    _ncpu: int = field(default=settings.NCPU, init=False, repr=False)
    _region: Region = field(init=False, repr=False)
    _ylm: np.ndarray = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.N = self.L * self.L
        self.region = Region(mask_name=self.mask_name)
        super().__post_init__()

    def _create_annotations(self) -> None:
        pass

    def _create_fn_name(self) -> None:
        self.name = f"slepian_{self.mask_name}"

    def _create_mask(self) -> None:
        self.mask = create_mask_region(self.resolution, self.region)

    def _create_matrix_location(self) -> None:
        self.matrix_location = (
            _arbitrary_path / "matrices" / f"D_{self.mask_name}_L{self.L}.npy"
        )

    def _solve_eigenproblem(self) -> None:
        D = self._load_D_matrix()
        eigenvalues, eigenvectors = np.linalg.eigh(D)
        self.eigenvalues, self.eigenvectors = self._clean_evals_and_evecs(
            eigenvalues, eigenvectors
        )

    def _load_D_matrix(self) -> np.ndarray:
        """
        if the D matrix already exists load it
        otherwise create it and save the result
        """
        # check if matrix already exists
        if Path(self.matrix_location).exists():
            D = np.load(self.matrix_location)
        else:
            if self.ncpu == 1:
                D = self._matrix_serial()
            else:
                D = self._matrix_parallel()

            # save to speed up for future
            if settings.SAVE_MATRICES:
                np.save(self.matrix_location, D)

        return D

    def _matrix_serial(self) -> np.ndarray:
        """
        computes the D matrix in serial
        """
        # initialise real and imaginary matrices
        D_r = np.zeros((self.N, self.N))
        D_i = np.zeros((self.N, self.N))

        for i in range(self.N):
            self._matrix_helper(D_r, D_i, i)

        # combine real and imaginary parts
        D = D_r + 1j * D_i

        return D

    def _matrix_parallel(self) -> np.ndarray:
        """
        computes the D matrix in parallel
        """
        # initialise real and imaginary matrices
        D_r = np.zeros((self.N, self.N))
        D_i = np.zeros((self.N, self.N))

        # create shared memory block
        shm_r = SharedMemory(create=True, size=D_r.nbytes)
        shm_i = SharedMemory(create=True, size=D_i.nbytes)
        # create a array backed by shared memory
        D_r_ext = np.ndarray(D_r.shape, dtype=D_r.dtype, buffer=shm_r.buf)
        D_i_ext = np.ndarray(D_i.shape, dtype=D_i.dtype, buffer=shm_i.buf)

        def func(chunk: List[int]) -> None:
            """
            calculate D matrix components for each chunk
            """
            # attach to the existing shared memory block
            ex_shm_r = SharedMemory(name=shm_r.name)
            ex_shm_i = SharedMemory(name=shm_i.name)
            D_r_int = np.ndarray(D_r.shape, dtype=D_r.dtype, buffer=ex_shm_r.buf)
            D_i_int = np.ndarray(D_i.shape, dtype=D_i.dtype, buffer=ex_shm_i.buf)

            # deal with chunk
            for i in chunk:
                self._matrix_helper(D_r_int, D_i_int, i)

            # clean up shared memory
            ex_shm_r.close()
            ex_shm_i.close()

        # split up L range to maximise effiency
        chunks = split_L_into_chunks(self.N, self.ncpu)

        # initialise pool and apply function
        with Pool(processes=self.ncpu) as p:
            p.map(func, chunks)

        # retrieve from parallel function
        D = D_r_ext + 1j * D_i_ext

        # Free and release the shared memory block at the very end
        shm_r.close()
        shm_r.unlink()
        shm_i.close()
        shm_i.unlink()

        return D

    def _matrix_helper(self, D_r: np.ndarray, D_i: np.ndarray, i: int) -> None:
        """
        used in both serial and parallel calculations

        the hack with splitting into real and imaginary parts
        is not required for the serial case but here for ease
        """
        # fill in diagonal components
        integral = self._integral(i, i)
        D_r[i][i] = integral.real
        D_i[i][i] = integral.imag
        _, m_i = ssht.ind2elm(i)

        for j in range(i + 1, self.N):
            ell_j, m_j = ssht.ind2elm(j)
            # if possible to use previous calculations
            if m_i == 0 and m_j != 0 and ell_j < self.L:
                # if positive m then use conjugate relation
                if m_j > 0:
                    integral = self._integral(i, j)
                    D_r[i][j] = integral.real
                    D_i[i][j] = integral.imag
                    D_r[j][i] = D_r[i][j]
                    D_i[j][i] = -D_i[i][j]
                    k = ssht.elm2ind(ell_j, -m_j)
                    D_r[i][k] = (-1) ** m_j * D_r[i][j]
                    D_i[i][k] = (-1) ** (m_j + 1) * D_i[i][j]
                    D_r[k][i] = D_r[i][k]
                    D_i[k][i] = -D_i[i][k]
            else:
                integral = self._integral(i, j)
                D_r[i][j] = integral.real
                D_i[i][j] = integral.imag
                D_r[j][i] = D_r[i][j]
                D_i[j][i] = -D_i[i][j]

    def _integral(self, i: int, j: int) -> complex:
        flm = self._f(i)
        glm = self._f(j)
        integration = integrate_sphere(
            self.L, self.resolution, flm, glm, mask_boosted=self.mask, glm_conj=True
        )
        return integration

    def _f(self, i: int) -> np.ndarray:
        flm = np.zeros(self.L * self.L, dtype=complex)
        flm[i] = 1
        return flm

    @staticmethod
    def _clean_evals_and_evecs(
        eigenvalues: np.ndarray, eigenvectors: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        need eigenvalues and eigenvectors to be in a certain format
        """
        # eigenvalues should be real
        eigenvalues = eigenvalues.real

        # Sort eigenvalues and eigenvectors in descending order of eigenvalues
        idx = eigenvalues.argsort()[::-1]
        eigenvalues = eigenvalues[idx]
        eigenvectors = eigenvectors[:, idx].conj().T

        # ensure first element of each eigenvector is positive
        eigenvectors *= np.where(eigenvectors[:, 0] < 0, -1, 1)[:, np.newaxis]

        # find repeating eigenvalues and ensure orthorgonality
        pairs = np.where(np.abs(np.diff(eigenvalues)) < 1e-14)[0] + 1
        eigenvectors[pairs] *= 1j

        return eigenvalues, eigenvectors

    @property  # type: ignore
    def mask_name(self) -> str:
        return self._mask_name

    @mask_name.setter
    def mask_name(self, mask_name: str) -> None:
        self._mask_name = mask_name

    @property
    def N(self) -> int:
        return self._N

    @N.setter
    def N(self, N: int) -> None:
        self._N = N

    @property  # type: ignore
    def ncpu(self) -> int:
        return self._ncpu

    @ncpu.setter
    def ncpu(self, ncpu: int) -> None:
        if isinstance(ncpu, property):
            # initial value not specified, use default
            # https://stackoverflow.com/a/61480946/7359333
            ncpu = SlepianArbitrary._ncpu
        self._ncpu = ncpu

    @property
    def region(self) -> Region:
        return self._region

    @region.setter
    def region(self, region: Region) -> None:
        self._region = region
