from pys2sleplet.plotting.create_plot import Plot
from pys2sleplet.utils.denoising import denoising_axisym

B = 2
J_MIN = 0
L = 128
N_SIGMA = 3
SNR_IN = 10


def main() -> None:
    """
    reproduce the denoising demo from s2let paper
    """
    fun = "earth"
    f, _, _ = denoising_axisym(fun, L, B, J_MIN, N_SIGMA, SNR_IN)
    name = f"{fun}_denoised_axisym_L{L}"
    Plot(f, L, name).execute()


if __name__ == "__main__":
    main()
