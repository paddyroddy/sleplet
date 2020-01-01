import multiprocessing.sharedctypes as sct
from multiprocessing import Pool
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pyssht as ssht
from scipy.special import factorial as fact

from pys2sleplet.slepian.slepian_specific import SlepianSpecific
from pys2sleplet.utils.vars import ENVS, SLEPIAN


class SlepianPolarCap(SlepianSpecific):
    def __init__(self, L: int, order: int = 0):
        super().__init__(L)
        self.matrix_filename = (
            Path(__file__).resolve().parents[1]
            / "data"
            / "polar"
            / SlepianSpecific.matrix_filename.name
        )
        self.order = order

    @property
    def order(self) -> int:
        return self.__order

    @order.setter
    def order(self, var: int) -> None:
        # test if order is an integer
        if not isinstance(var, int):
            raise ValueError("Slepian polar cap order should be an integer")

        # check order is in correct range
        if abs(var) >= self.L:
            raise ValueError(
                f"Slepian polar cap order magnitude should be less than {self.L}"
            )
        self.__order = var

    @staticmethod
    def Wigner3j(l1: int, l2: int, l3: int, m1: int, m2: int, m3: int) -> float:
        """
        Syntax:
        s = Wigner3j (l1, l2, l3, m1, m2, m3)

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

    def Dm_matrix_serial(self, m: int, P: np.ndarray) -> np.ndarray:
        """
        Syntax:
        Dm = Dm_matrix_serial(m, P)

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
                        self.Wigner3j(l, n, p, 0, 0, 0)
                        * self.Wigner3j(l, n, p, m, 0, -m)
                        * (A - Pl[ell == n + 1])
                    )
                Dm[i, j] = (
                    self.polar_gap_modification(l, p)
                    * np.sqrt((2 * l + 1) * (2 * p + 1))
                    * c
                )
                Dm[j, i] = Dm[i, j]

        Dm *= (-1) ** m / 2

        return Dm

    def Dm_matrix_parallel(self, m: int, P: np.ndarray, ncpu: int) -> np.ndarray:
        """
        Syntax:
        Dm = Dm_matrix_parallel(m, P, ncpu)

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

        # create arrays to store final and intermediate steps
        result = np.ctypeslib.as_ctypes(Dm)
        shared_array = sct.RawArray(result._type_, result)

        def func(chunk: List[int]) -> None:
            """
            calculate D matrix components for each chunk
            """
            # temporary store
            tmp = np.ctypeslib.as_array(shared_array)

            # deal with chunk
            for i in chunk:
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
                            self.Wigner3j(l, n, p, 0, 0, 0)
                            * self.Wigner3j(l, n, p, m, 0, -m)
                            * (A - Pl[ell == n + 1])
                        )
                    tmp[i, j] = (
                        self.polar_gap_modification(l, p)
                        * np.sqrt((2 * l + 1) * (2 * p + 1))
                        * c
                    )
                    tmp[j, i] = tmp[i, j]

        # split up L range to maximise effiency
        arr = np.arange(self.L - m)
        size = len(arr)
        arr[size // 2 : size] = arr[size // 2 : size][::-1]
        chunks = [np.sort(arr[i::ncpu]) for i in range(ncpu)]

        # initialise pool and apply function
        with Pool(processes=ncpu) as p:
            p.map(func, chunks)

        # retrieve from parallel function
        Dm = np.ctypeslib.as_array(shared_array) * (-1) ** m / 2

        return Dm

    @staticmethod
    def polar_gap_modification(ell1: int, ell2: int) -> int:
        factor = 1 + SLEPIAN["POLAR_GAP"] * (-1) ** (ell1 + ell2)
        return factor

    def eigenproblem(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        """
        # create emm vector
        emm = np.zeros(2 * self.L * 2 * self.L)
        k = 0
        for l in range(2 * self.L):
            M = 2 * l + 1
            emm[k : k + M] = np.arange(-l, l + 1)
            k = k + M

        # check if matrix already exists
        if Path(self.matrix_filename).exists():
            Dm = np.load(self.matrix_filename)
        else:
            # create Legendre polynomials table
            Plm = ssht.create_ylm(self.theta_max, 0, 2 * self.L).real.reshape(-1)
            ind = emm == 0
            l = np.arange(2 * self.L).reshape(1, -1)
            Pl = np.sqrt((4 * np.pi) / (2 * l + 1)) * Plm[ind]
            P = np.concatenate((Pl, l))

            # Computing order 'm' Slepian matrix
            if ENVS["N_CPU"] == 1:
                Dm = self.Dm_matrix_serial(abs(self.order), P)
            else:
                Dm = self.Dm_matrix_parallel(abs(self.order), P, ENVS["N_CPU"])

            # save to speed up for future
            if ENVS["SAVE_MATRICES"]:
                np.save(self.matrix_filename, Dm)

        # solve eigenproblem for order 'm'
        eigenvalues, gl = np.linalg.eigh(Dm)

        # eigenvalues should be real
        eigenvalues = eigenvalues.real

        # Sort eigenvalues and eigenvectors in descending order of eigenvalues
        idx = eigenvalues.argsort()[::-1]
        eigenvalues = eigenvalues[idx]
        gl = np.conj(gl[:, idx])

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

    def annotations(self) -> List[dict]:
        """
        annotations for the plotly plot
        """
        annotation = []
        config = dict(arrowhead=6, ax=5, ay=5)
        # check if dealing with small polar cap
        if self.theta_max <= 45:
            ndots = 12
            theta = np.array(np.deg2rad(self.theta_max))
            for i in range(ndots):
                phi = np.array(2 * np.pi / ndots * (i + 1))
                x, y, z = ssht.s2_to_cart(theta, phi)
                annotation.append({**dict(x=x, y=y, z=z, arrowcolor="black"), **config})
            # check if dealing with polar gap
            if self.polar_gap:
                theta_bottom = np.array(np.pi - np.deg2rad(self.theta_max))
                for i in range(ndots):
                    phi = np.array(2 * np.pi / ndots * (i + 1))
                    x, y, z = ssht.s2_to_cart(theta_bottom, phi)
                    annotation.append(
                        {**dict(x=x, y=y, z=z, arrowcolor="white"), **config}
                    )
        return annotation