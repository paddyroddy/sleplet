from plotting import Plotting
from fractions import Fraction
import numpy as np
import os
import sys
from typing import List, Tuple

sys.path.append(os.path.join(os.environ["SSHT"], "src", "python"))
import pyssht as ssht


class SiftingConvolution:
    def __init__(
        self,
        flm: np.ndarray,
        flm_name: str,
        config: dict,
        glm: np.ndarray = None,
        glm_name: str = None,
    ) -> None:
        self.annotation = config["annotation"]
        self.auto_open = config["auto_open"]
        self.flm_name = flm_name
        self.flm = flm
        self.glm = glm
        if self.glm is not None:
            self.glm_name = glm_name
        self.L = config["L"]
        self.location = os.path.realpath(
            os.path.join(os.getcwd(), os.path.dirname(__file__))
        )
        self.method = config["sampling"]
        self.reality = config["reality"]
        self.resolution = self.calc_resolution(self.L)
        self.routine = config["routine"]
        self.save_fig = config["save_fig"]
        self.type = config["type"]

    # -----------------------------------
    # ---------- flm functions ----------
    # -----------------------------------

    def rotation(
        self, flm: np.ndarray, alpha: float, beta: float, gamma: float
    ) -> np.ndarray:
        """
        rotates given flm on the sphere by alpha/beta/gamma
        """
        flm_rot = ssht.rotate_flms(flm, alpha, beta, gamma, self.L)
        return flm_rot

    def translation(self, flm: np.ndarray) -> np.ndarray:
        """
        translates given flm on the sphere by alpha/beta
        """
        # numpy binary filename
        filename = os.path.join(
            self.location,
            "npy",
            (
                f"trans_dd_L-{self.L}_"
                f"{self.filename_angle(self.alpha_pi_fraction,self.beta_pi_fraction)}"
                f"samp-{self.method}.npy"
            ),
        )

        # check if file of translated dirac delta already
        # exists otherwise calculate translated dirac delta
        if os.path.exists(filename):
            glm = np.load(filename)
        else:
            glm = np.conj(ssht.create_ylm(self.beta, self.alpha, self.L))
            glm = glm.reshape(glm.size)
            # save to speed up for future
            np.save(filename, glm)

        # convolve with flm
        if self.flm_name == "dirac_delta":
            flm_conv = glm
        else:
            flm_conv = self.convolution(flm, glm)
        return flm_conv

    def convolution(self, flm: np.ndarray, glm: np.ndarray) -> np.ndarray:
        """
        computes the sifting convolution of two arrays
        """
        # translation/convolution are not real for general
        # function so turn off reality except for Dirac delta
        self.reality = False

        return flm * np.conj(glm)

    # ----------------------------------------
    # ---------- plotting function ----------
    # ----------------------------------------

    def plot(
        self,
        alpha_pi_fraction: float = 0.75,
        beta_pi_fraction: float = 0.25,
        gamma_pi_fraction: float = 0,
    ) -> None:
        """
        master plotting method
        """
        # setup
        gamma = gamma_pi_fraction * np.pi
        filename = f"{self.flm_name}_L-{self.L}_"

        # calculate nearest index of alpha/beta for translation
        self.calc_nearest_grid_point(alpha_pi_fraction, beta_pi_fraction)

        # test for plotting routine
        if self.routine == "north":
            flm = self.flm
        elif self.routine == "rotate":
            # adjust filename
            filename += (
                f"{self.routine}_"
                f"{self.filename_angle(alpha_pi_fraction, beta_pi_fraction, gamma_pi_fraction)}"
            )
            # rotate by alpha, beta
            flm = self.rotation(self.flm, self.alpha, self.beta, gamma)
        elif self.routine == "translate":
            # adjust filename
            # don't add gamma if translation
            filename += (
                f"{self.routine}_"
                f"{self.filename_angle(alpha_pi_fraction, beta_pi_fraction)}"
            )
            # translate by alpha, beta
            flm = self.translation(self.flm)

        if self.glm is not None:
            # perform convolution
            flm = self.convolution(flm, self.glm)
            # adjust filename
            filename += f"convolved_{self.glm_name}_L-{self.L}_"

        # boost resolution
        if self.resolution != self.L:
            flm = self.resolution_boost(flm)

        # add sampling/resolution to filename
        filename += f"samp-{self.method}_res-{self.resolution}_"

        # inverse & plot
        f = ssht.inverse(flm, self.resolution, Method=self.method, Reality=self.reality)

        # check for plotting type
        if self.type == "real":
            f = f.real
        elif self.type == "imag":
            f = f.imag
        elif self.type == "abs":
            f = abs(f)
        elif self.type == "sum":
            f = f.real + f.imag

        # do plot
        filename += self.type
        # self.plotly_plot(plot, filename, self.save_fig)
        plotting = Plotting(
            f,
            self.resolution,
            filename,
            method=self.method,
            annotations=self.annotations(),
            auto_open=self.auto_open,
            save_fig=self.save_fig,
        )
        plotting.plotly_plot()

    # --------------------------------------------------
    # ---------- translation helper function ----------
    # --------------------------------------------------

    def calc_nearest_grid_point(
        self, alpha_pi_fraction: float = 0, beta_pi_fraction: float = 0
    ) -> None:
        """
        calculate nearest index of alpha/beta for translation
        this is due to calculating omega' through the pixel
        values - the translation needs to be at the same position
        as the rotation such that the difference error is small
        """
        thetas, phis = ssht.sample_positions(self.L, Method=self.method)
        pix_j = (np.abs(phis - alpha_pi_fraction * np.pi)).argmin()
        pix_i = (np.abs(thetas - beta_pi_fraction * np.pi)).argmin()
        self.alpha = phis[pix_j]
        self.beta = thetas[pix_i]
        self.alpha_pi_fraction = alpha_pi_fraction
        self.beta_pi_fraction = beta_pi_fraction

    # -----------------------------------------------
    # ---------- plotting helper functions ----------
    # -----------------------------------------------

    def annotations(self) -> List[dict]:
        if self.annotation:
            # if north alter values to point at correct point
            if self.routine == "north":
                x, y, z = 0, 0, 1
            else:
                x, y, z = ssht.s2_to_cart(self.beta, self.alpha)

            # initialise array and standard arrow
            annotation = []
            config = dict(arrowcolor="white", yshift=5)
            arrow = {**dict(x=x, y=y, z=z), **config}

            # various switch cases for annotation
            if self.flm_name.startswith("elongated_gaussian"):
                if self.routine == "translate":
                    annotation.append({**config, **dict(x=-x, y=y, z=z)})
                    annotation.append({**config, **dict(x=x, y=-y, z=z)})
            elif self.flm_name == "dirac_delta":
                if self.type != "imag":
                    annotation.append(arrow)
            elif "gaussian" in self.flm_name:
                if self.routine != "translate":
                    if self.type != "imag":
                        annotation.append(arrow)

            # if convolution then remove annotation
            if self.glm is not None:
                annotation = []
        else:
            annotation = []
        return annotation

    @staticmethod
    def pi_in_filename(numerator: int, denominator: int) -> str:
        """
        create filename for angle as multiple of pi
        """
        # if whole number
        if denominator == 1:
            # if 1 * pi
            if numerator == 1:
                filename = "pi"
            else:
                filename = f"{numerator}pi"
        else:
            filename = f"{numerator}pi{denominator}"
        return filename

    @staticmethod
    def get_angle_num_dem(angle_fraction: float) -> Tuple[int, int]:
        """
        ger numerator and denominator for a given decimal
        """
        angle = Fraction(angle_fraction).limit_denominator()
        return angle.numerator, angle.denominator

    @staticmethod
    def calc_resolution(L: int) -> int:
        """
        calculate appropriate resolution for given L
        """
        if L == 1:
            exponent = 6
        elif L < 4:
            exponent = 5
        elif L < 8:
            exponent = 4
        elif L < 128:
            exponent = 3
        elif L < 512:
            exponent = 2
        elif L < 1024:
            exponent = 1
        else:
            exponent = 0
        return L * 2 ** exponent

    def resolution_boost(self, flm: np.ndarray) -> np.ndarray:
        """
        calculates a boost in resoltion for given flm
        """
        boost = self.resolution * self.resolution - self.L * self.L
        flm_boost = np.pad(flm, (0, boost), "constant")
        return flm_boost

    def filename_angle(
        self,
        alpha_pi_fraction: float,
        beta_pi_fraction: float,
        gamma_pi_fraction: float = 0,
    ) -> str:
        """
        middle part of filename
        """
        # get numerator/denominator for filename
        alpha_num, alpha_den = self.get_angle_num_dem(alpha_pi_fraction)
        beta_num, beta_den = self.get_angle_num_dem(beta_pi_fraction)
        gamma_num, gamma_den = self.get_angle_num_dem(gamma_pi_fraction)

        # if alpha = beta = 0
        if not alpha_num and not beta_num:
            filename = "alpha-0_beta-0_"
        # if alpha = 0
        elif not alpha_num:
            filename = f"alpha-0_beta-{self.pi_in_filename(beta_num, beta_den)}_"
        # if beta = 0
        elif not beta_num:
            filename = f"alpha-{self.pi_in_filename(alpha_num, alpha_den)}_beta-0_"
        # if alpha != 0 && beta !=0
        else:
            filename = (
                f"alpha-{self.pi_in_filename(alpha_num, alpha_den)}"
                f"_beta-{self.pi_in_filename(beta_num, beta_den)}_"
            )

        # if rotation with gamma != 0
        if gamma_num:
            filename += f"gamma-{self.pi_in_filename(gamma_num, gamma_den)}_"
        return filename
