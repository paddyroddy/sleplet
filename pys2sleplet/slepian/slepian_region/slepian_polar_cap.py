from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pyssht as ssht
from multiprocess import Pool
from multiprocess.shared_memory import SharedMemory
from scipy.special import factorial as fact

from pys2sleplet.slepian.slepian_functions import SlepianFunctions
from pys2sleplet.utils.bool_methods import is_small_polar_cap
from pys2sleplet.utils.config import config
from pys2sleplet.utils.mask_methods import create_mask_region
from pys2sleplet.utils.parallel_methods import split_L_into_chunks
from pys2sleplet.utils.region import Region
from pys2sleplet.utils.vars import (
    ANNOTATION_COLOUR,
    ANNOTATION_DOTS,
    ANNOTATION_SECOND_COLOUR,
    ARROW_STYLE,
    GAP_DEFAULT,
    ORDER_DEFAULT,
)

_file_location = Path(__file__).resolve()


@dataclass
class SlepianPolarCap(SlepianFunctions):
    theta_max: float
    order: int
    gap: bool
    ncpu: int
    _gap: bool = field(default=GAP_DEFAULT, init=False, repr=False)
    _order: int = field(default=ORDER_DEFAULT, init=False, repr=False)
    _name_ending: str = field(init=False, repr=False)
    _ncpu: int = field(default=config.NCPU, init=False, repr=False)
    _region: Region = field(init=False, repr=False)
    _theta_max: float = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.region = Region(theta_max=self.theta_max, order=self.order)
        self.name_ending = f"{self.region.name_ending}_m{self.order}"
        super().__post_init__()

    def _create_annotations(self) -> None:
        if is_small_polar_cap(self.theta_max):
            theta_top = np.array([self.theta_max])
            theta_bottom = np.array([np.pi - self.theta_max])
            for i in range(ANNOTATION_DOTS):
                self._add_to_annotation(theta_top, i, ANNOTATION_COLOUR)

                if self.gap:
                    for j in range(ANNOTATION_DOTS):
                        self._add_to_annotation(
                            theta_bottom, j, ANNOTATION_SECOND_COLOUR
                        )

    def _create_fn_name(self) -> None:
        self.name = f"slepian{self.name_ending}"

    def _create_mask(self) -> None:
        self.mask = create_mask_region(self.L, self.region)

    def _create_matrix_location(self) -> None:
        self.matrix_location = (
            _file_location.parents[2]
            / "data"
            / "slepian"
            / "polar"
            / f"D{self.name_ending}_L{self.L}.npy".replace("-", "")
        )

    def _solve_eigenproblem(self) -> None:
        emm = self._create_emm_vec()
        Dm = self._load_Dm_matrix(emm)

        # solve eigenproblem for order 'm'
        eigenvalues, gl = np.linalg.eigh(Dm)

        self.eigenvalues, self.eigenvectors = self._clean_evals_and_evecs(
            eigenvalues, gl, emm
        )

    def _add_to_annotation(self, theta: np.ndarray, i: int, colour: str) -> None:
        """
        add to annotation list for given theta
        """
        phi = np.array([2 * np.pi / ANNOTATION_DOTS * (i + 1)])
        x, y, z = ssht.s2_to_cart(theta, phi)
        self.annotations.append(
            {**dict(x=x[0], y=y[0], z=z[0], arrowcolor=colour), **ARROW_STYLE}
        )

    def _create_emm_vec(self) -> np.ndarray:
        """
        create emm vector for eigenproblem
        """
        emm = np.zeros(2 * self.L * 2 * self.L)
        k = 0

        for l in range(2 * self.L):
            M = 2 * l + 1
            emm[k : k + M] = np.arange(-l, l + 1)
            k = k + M
        return emm

    def _load_Dm_matrix(self, emm: np.ndarray) -> np.ndarray:
        """
        if the Dm matrix already exists load it
        otherwise create it and save the result
        """
        # check if matrix already exists
        if Path(self.matrix_location).exists():
            Dm = np.load(self.matrix_location)
        else:
            P = self._create_legendre_polynomials_table(emm)

            # Computing order 'm' Slepian matrix
            if self.ncpu == 1:
                Dm = self._dm_matrix_serial(abs(self.order), P)
            else:
                Dm = self._dm_matrix_parallel(abs(self.order), P)

            # save to speed up for future
            if config.SAVE_MATRICES:
                np.save(self.matrix_location, Dm)

        return Dm

    def _create_legendre_polynomials_table(self, emm: np.ndarray) -> np.ndarray:
        """
        create Legendre polynomials table for matrix calculation
        """
        Plm = ssht.create_ylm(self.theta_max, 0, 2 * self.L).real.reshape(-1)
        ind = emm == 0
        l = np.arange(2 * self.L).reshape(1, -1)
        Pl = np.sqrt((4 * np.pi) / (2 * l + 1)) * Plm[ind]
        P = np.concatenate((Pl, l))
        return P

    def _dm_matrix_serial(self, m: int, P: np.ndarray) -> np.ndarray:
        """
        Syntax:
        Dm = _dm_matrix_serial(m, P)

        Input:
        m  =  order
        P(:,1)  =  Pl = Legendre Polynomials column vector for l = 0 : L-1
        P(:,2)  =  ell values vector

        Output:
        Dm = (L - m) square Slepian matrix for order m

        Description:
        This piece of code computes the Slepian matrix, Dm, for order m and all
        degrees, using the formulation given in "Spatiospectral Concentration on
        a Sphere" by F.J. Simons, F.A. Dahlen and M.A. Wieczorek.
        """
        Dm = np.zeros((self.L - m, self.L - m))
        Pl, ell = P
        lvec = np.arange(m, self.L)

        for i in range(self.L - m):
            self._dm_matrix_helper(Dm, i, m, lvec, Pl, ell)

        Dm *= (-1) ** m / 2

        return Dm

    def _dm_matrix_parallel(self, m: int, P: np.ndarray) -> np.ndarray:
        """
        Syntax:
        Dm = _dm_matrix_parallel(m, P)

        Input:
        m  =  order
        P(:,1)  =  Pl = Legendre Polynomials column vector for l = 0 : L-1
        P(:,2)  =  ell values vector

        Output:
        Dm = (L - m) square Slepian matrix for order m

        Description:
        This piece of code computes the Slepian matrix, Dm, for order m and all
        degrees, using the formulation given in "Spatiospectral Concentration on
        a Sphere" by F.J. Simons, F.A. Dahlen and M.A. Wieczorek.
        """
        Dm = np.zeros((self.L - m, self.L - m))
        Pl, ell = P
        lvec = np.arange(m, self.L)

        # create shared memory block
        shm = SharedMemory(create=True, size=Dm.nbytes)
        # create a array backed by shared memory
        Dm_ext = np.ndarray(Dm.shape, dtype=Dm.dtype, buffer=shm.buf)

        def func(chunk: List[int]) -> None:
            """
            calculate D matrix components for each chunk
            """
            # attach to the existing shared memory block
            ex_shm = SharedMemory(name=shm.name)
            Dm_int = np.ndarray(Dm.shape, dtype=Dm.dtype, buffer=ex_shm.buf)

            # deal with chunk
            for i in chunk:
                self._dm_matrix_helper(Dm_int, i, m, lvec, Pl, ell)

            # clean up shared memory
            ex_shm.close()

        # split up L range to maximise effiency
        chunks = split_L_into_chunks(self.L - m, self.ncpu)

        # initialise pool and apply function
        with Pool(processes=self.ncpu) as p:
            p.map(func, chunks)

        # retrieve from parallel function
        Dm = Dm_ext * (-1) ** m / 2

        # Free and release the shared memory block at the very end
        shm.close()
        shm.unlink()

        return Dm

    def _dm_matrix_helper(
        self,
        Dm: np.ndarray,
        i: int,
        m: int,
        lvec: np.ndarray,
        Pl: np.ndarray,
        ell: np.ndarray,
    ) -> None:
        """
        used in both serial and parallel calculations
        """
        l = lvec[i]
        for j in range(i, self.L - m):
            p = lvec[j]
            c = 0
            for n in range(abs(l - p), l + p + 1):
                if n - 1 == -1:
                    A = 1
                else:
                    A = Pl[ell == n - 1]
                c += (
                    self._wigner3j(l, n, p, 0, 0, 0)
                    * self._wigner3j(l, n, p, m, 0, -m)
                    * (A - Pl[ell == n + 1])
                )
            Dm[i, j] = (
                self._polar_gap_modification(l, p)
                * np.sqrt((2 * l + 1) * (2 * p + 1))
                * c
            )
            Dm[j, i] = Dm[i, j]

    @staticmethod
    def _wigner3j(l1: int, l2: int, l3: int, m1: int, m2: int, m3: int) -> float:
        """
        Syntax:
        s = _wigner3j (l1, l2, l3, m1, m2, m3)

        Input:
        l1  =  first degree in Wigner 3j symbol
        l2  =  second degree in Wigner 3j symbol
        l3  =  third degree in Wigner 3j symbol
        m1  =  first order in Wigner 3j symbol
        m2  =  second order in Wigner 3j symbol
        m3  =  third order in Wigner 3j symbol

        Output:
        s  =  Wigner 3j symbol for l1,m1; l2,m2; l3,m3

        Description:
        Computes Wigner 3j symbol using Racah formula
        """
        if (
            2 * l1 != np.floor(2 * l1)
            or 2 * l2 != np.floor(2 * l2)
            or 2 * l3 != np.floor(2 * l3)
            or 2 * m1 != np.floor(2 * m1)
            or 2 * m2 != np.floor(2 * m2)
            or 2 * m3 != np.floor(2 * m3)
        ):
            raise Exception("Arguments must either be integer or half-integer!")

        if (
            m1 + m2 + m3 != 0
            or l3 < abs(l1 - l2)
            or l3 > (l1 + l2)
            or abs(m1) > abs(l1)
            or abs(m2) > abs(l2)
            or abs(m3) > abs(l3)
            or l1 + l2 + l3 != np.floor(l1 + l2 + l3)
        ):
            s = 0
        else:
            t1 = l2 - l3 - m1
            t2 = l1 - l3 + m2
            t3 = l1 + l2 - l3
            t4 = l1 - m1
            t5 = l2 + m2

            tmin = max(0, max(t1, t2))
            tmax = min(t3, min(t4, t5))

            s = 0
            # sum is over all those t for which the following factorials have
            # non-zero arguments.
            for t in range(tmin, tmax + 1):
                s += (-1) ** t / (
                    fact(t, exact=False)
                    * fact(t - t1, exact=False)
                    * fact(t - t2, exact=False)
                    * fact(t3 - t, exact=False)
                    * fact(t4 - t, exact=False)
                    * fact(t5 - t, exact=False)
                )

            triangle_coefficient = (
                fact(l1 + l2 - l3, exact=False)
                * fact(l1 - l2 + l3, exact=False)
                * fact(-l1 + l2 + l3, exact=False)
                / fact(l1 + l2 + l3 + 1, exact=False)
            )

            s *= (
                np.float_power(-1, l1 - l2 - m3)
                * np.sqrt(triangle_coefficient)
                * np.sqrt(
                    fact(l1 + m1, exact=False)
                    * fact(l1 - m1, exact=False)
                    * fact(l2 + m2, exact=False)
                    * fact(l2 - m2, exact=False)
                    * fact(l3 + m3, exact=False)
                    * fact(l3 - m3, exact=False)
                )
            )
        return s

    def _polar_gap_modification(self, ell1: int, ell2: int) -> int:
        """
        eq 67 - Spherical Slepian functions and the polar gap in geodesy
        multiply by 1 + (-1)*(ell+ell')
        """
        factor = 1 + self.gap * (-1) ** (ell1 + ell2)
        return factor

    def _clean_evals_and_evecs(
        self, eigenvalues: np.ndarray, gl: np.ndarray, emm: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        need eigenvalues and eigenvectors to be in a certain format
        """
        # eigenvalues should be real
        eigenvalues = eigenvalues.real

        # Sort eigenvalues and eigenvectors in descending order of eigenvalues
        idx = eigenvalues.argsort()[::-1]
        eigenvalues = eigenvalues[idx]
        gl = gl[:, idx].conj()

        # put back in full D space for harmonic transform
        emm = emm[: self.L * self.L]
        ind = np.tile(emm == self.order, (self.L - abs(self.order), 1))
        eigenvectors = np.zeros(
            (self.L - abs(self.order), self.L * self.L), dtype=complex
        )
        eigenvectors[ind] = gl.T.flatten()

        # ensure first element of each eigenvector is positive
        eigenvectors *= np.where(eigenvectors[:, 0] < 0, -1, 1)[:, np.newaxis]

        # if -ve 'm' find orthogonal eigenvectors to +ve 'm' eigenvectors
        if self.order < 0:
            eigenvectors *= 1j

        return eigenvalues, eigenvectors

    @property  # type: ignore
    def gap(self) -> bool:
        return self._gap

    @gap.setter
    def gap(self, gap: bool) -> None:
        if isinstance(gap, property):
            # initial value not specified, use default
            # https://stackoverflow.com/a/61480946/7359333
            gap = SlepianPolarCap._gap
        self._gap = gap

    @property
    def name_ending(self) -> str:
        return self._name_ending

    @name_ending.setter
    def name_ending(self, name_ending: str) -> None:
        self._name_ending = name_ending

    @property  # type: ignore
    def ncpu(self) -> int:
        return self._ncpu

    @ncpu.setter
    def ncpu(self, ncpu: int) -> None:
        if isinstance(ncpu, property):
            # initial value not specified, use default
            # https://stackoverflow.com/a/61480946/7359333
            ncpu = SlepianPolarCap._ncpu
        self._ncpu = ncpu

    @property  # type:ignore
    def order(self) -> int:
        return self._order

    @order.setter
    def order(self, order: int) -> None:
        if isinstance(order, property):
            # initial value not specified, use default
            # https://stackoverflow.com/a/61480946/7359333
            order = SlepianPolarCap._order
        if abs(order) >= self.L:
            raise ValueError(f"Order magnitude should be less than {self.L}")
        self._order = order

    @property
    def region(self) -> Region:
        return self._region

    @region.setter
    def region(self, region: Region) -> None:
        self._region = region

    @property  # type:ignore
    def theta_max(self) -> float:
        return self._theta_max

    @theta_max.setter
    def theta_max(self, theta_max: float) -> None:
        if theta_max == 0:
            raise ValueError("theta_max cannot be zero")
        self._theta_max = theta_max