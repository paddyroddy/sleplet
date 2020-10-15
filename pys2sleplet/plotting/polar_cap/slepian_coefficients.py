from pathlib import Path

import numpy as np
import seaborn as sns
from matplotlib import pyplot as plt

from pys2sleplet.plotting.inputs import THETA_MAX
from pys2sleplet.plotting.plotting_utils import (
    earth_region_harmonic_coefficients,
    earth_region_slepian_coefficients,
)
from pys2sleplet.utils.plot_methods import save_plot

L = 19

file_location = Path(__file__).resolve()
fig_path = file_location.parents[2] / "figures"
sns.set(context="paper")


def main() -> None:
    """
    creates a plot of Slepian coefficients against rank
    """
    flm = earth_region_harmonic_coefficients(L, THETA_MAX)
    f_p = np.sort(earth_region_slepian_coefficients(L, THETA_MAX))[::-1]
    ax = plt.gca()
    sns.scatterplot(
        x=range(L ** 2), y=f_p, ax=ax, label="slepian", linewidth=0, marker="*"
    )
    sns.scatterplot(
        x=range(L ** 2), y=flm, ax=ax, label="harmonic", linewidth=0, marker="."
    )
    ax.set_xlabel("coefficients")
    ax.set_ylabel("magnitude")
    save_plot(fig_path, f"fp_earth_polar{THETA_MAX}_L{L}")


if __name__ == "__main__":
    main()
