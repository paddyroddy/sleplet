from pathlib import Path

import numpy as np
import seaborn as sns
from matplotlib import pyplot as plt

from pys2sleplet.utils.plot_methods import save_plot

file_location = Path(__file__).resolve()
fig_path = file_location.parents[2] / "figures"
sns.set(context="paper")

DELTA_T = 0.001
FREQUENCIES = [5, 10, 15]
LENGTH = 0.512


def main() -> None:
    """
    plots a Dirac impulse and it's Fourier transform
    """
    amplitude = None
    for f in FREQUENCIES:
        wavelet = _ricker(f)
        amplitude = (
            np.concatenate([amplitude, wavelet]) if amplitude is not None else wavelet
        )
    plt.plot(amplitude)
    plt.xticks([])
    plt.xlabel(r"$t$")
    save_plot(fig_path, "ricker_wavelets")


def _ricker(freq: float) -> np.ndarray:
    """
    creates a Ricker wavelet
    """
    t = np.arange(-LENGTH / 2, (LENGTH - DELTA_T) / 2, DELTA_T)
    return (1.0 - 2.0 * (np.pi ** 2) * (freq ** 2) * (t ** 2)) * np.exp(
        -(np.pi ** 2) * (freq ** 2) * (t ** 2)
    )


if __name__ == "__main__":
    main()
