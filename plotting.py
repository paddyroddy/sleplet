import cmocean
import numpy as np
import os
from plotly.graph_objs import Figure, Layout, Surface
from plotly.graph_objs.layout import Margin, Scene
from plotly.graph_objs.layout.scene import XAxis, YAxis, ZAxis
import plotly.io as pio
import plotly.offline as py
import sys
from typing import List, Tuple

sys.path.append(os.path.join(os.environ["SSHT"], "src", "python"))
import pyssht as ssht


class Plotting:
    def __init__(
        self,
        f,
        resolution,
        filename,
        method="MW",
        annotations=[],
        auto_open=True,
        save_fig=False,
    ):
        self.annotations = annotations
        self.auto_open = auto_open
        self.f = f
        self.filename = filename
        self.location = os.path.realpath(
            os.path.join(os.getcwd(), os.path.dirname(__file__))
        )
        self.method = method
        self.resolution = resolution
        self.save_fig = save_fig

    def plotly_plot(self) -> None:
        """
        creates basic plotly plot rather than matplotlib
        """
        # get values from the setup
        x, y, z, f_plot, vmin, vmax = self._setup_plot(
            self.f, self.resolution, self.method
        )

        # appropriate zoom in on north pole
        zoom = 1.58
        camera = dict(eye=dict(x=-0.1 / zoom, y=-0.1 / zoom, z=2 / zoom))

        data = [
            Surface(
                x=x,
                y=y,
                z=z,
                surfacecolor=f_plot,
                colorscale=self._cmocean_to_plotly("solar"),
                cmin=vmin,
                cmax=vmax,
                colorbar=dict(
                    x=0.92, len=0.98, nticks=5, tickfont=dict(color="#666666", size=32)
                ),
            )
        ]

        axis = dict(
            title="", showgrid=False, zeroline=False, ticks="", showticklabels=False
        )

        layout = Layout(
            scene=Scene(
                dragmode="orbit",
                camera=camera,
                xaxis=XAxis(axis),
                yaxis=YAxis(axis),
                zaxis=ZAxis(axis),
                annotations=self.annotations,
            ),
            margin=Margin(l=0, r=0, b=0, t=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )

        fig = Figure(data=data, layout=layout)

        # if save_fig is true then print as png and pdf in their directories
        if self.save_fig:
            png_filename = os.path.join(
                self.location, "figures", "png", f"{self.filename}.png"
            )
            pio.write_image(fig, png_filename)
            pdf_filename = os.path.join(
                self.location, "figures", "pdf", f"{self.filename}.pdf"
            )
            pio.write_image(fig, pdf_filename)

        # create html and open if auto_open is true
        html_filename = os.path.join(
            self.location, "figures", "html", f"{self.filename}.html"
        )
        py.plot(fig, filename=html_filename, auto_open=self.auto_open)

    @staticmethod
    def _setup_plot(
        f: np.ndarray,
        resolution: int,
        method: str,
        close: bool = True,
        parametric: bool = False,
        parametric_scaling: List[float] = [0.0, 0.5],
        color_range: List[float] = None,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float, float]:
        """
        function which creates the data for the matplotlib/plotly plot
        """
        if method == "MW_pole":
            if len(f) == 2:
                f, f_sp = f
            else:
                f, f_sp, phi_sp = f

        (thetas, phis) = ssht.sample_positions(resolution, Method=method, Grid=True)

        if thetas.size != f.size:
            raise Exception("Band-limit L deos not match that of f")

        f_plot = f.copy()

        f_max = f_plot.max()
        f_min = f_plot.min()

        if color_range is None:
            vmin = f_min
            vmax = f_max
        else:
            vmin = color_range[0]
            vmax = color_range[1]
            f_plot[f_plot < color_range[0]] = color_range[0]
            f_plot[f_plot > color_range[1]] = color_range[1]
            f_plot[f_plot == -1.56e30] = np.nan

        # % Compute position scaling for parametric plot.
        if parametric:
            f_normalised = (f_plot - vmin / (vmax - vmin)) * parametric_scaling[
                1
            ] + parametric_scaling[0]

        # % Close plot.
        if close:
            (n_theta, n_phi) = ssht.sample_shape(resolution, Method=method)
            f_plot = np.insert(f_plot, n_phi, f[:, 0], axis=1)
            if parametric:
                f_normalised = np.insert(
                    f_normalised, n_phi, f_normalised[:, 0], axis=1
                )
            thetas = np.insert(thetas, n_phi, thetas[:, 0], axis=1)
            phis = np.insert(phis, n_phi, phis[:, 0], axis=1)

        # % Compute location of vertices.
        if parametric:
            (x, y, z) = ssht.spherical_to_cart(f_normalised, thetas, phis)
        else:
            (x, y, z) = ssht.s2_to_cart(thetas, phis)

        return x, y, z, f_plot, vmin, vmax

    @staticmethod
    def _cmocean_to_plotly(colour, pl_entries: int = 255) -> List[Tuple[float, str]]:
        """
        converts cmocean colourscale to a plotly colourscale
        """
        cmap = getattr(cmocean.cm, colour)

        h = 1 / (pl_entries - 1)
        pl_colorscale = []

        for k in range(pl_entries):
            C = list(map(np.uint8, np.array(cmap(k * h)[:3]) * 255))
            pl_colorscale.append((k * h, f"rgb{(C[0], C[1], C[2])}"))

        return pl_colorscale
