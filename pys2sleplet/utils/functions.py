from pys2sleplet.flm.kernels.dirac_delta import DiracDelta
from pys2sleplet.flm.kernels.elongated_gaussian import ElongatedGaussian
from pys2sleplet.flm.kernels.gaussian import Gaussian
from pys2sleplet.flm.kernels.harmonic_gaussian import HarmonicGaussian
from pys2sleplet.flm.kernels.identity import Identity
from pys2sleplet.flm.kernels.slepian import Slepian
from pys2sleplet.flm.kernels.spherical_harmonic import SphericalHarmonic
from pys2sleplet.flm.kernels.squashed_gaussian import SquashedGaussian
from pys2sleplet.flm.maps.earth import Earth
from pys2sleplet.flm.maps.wmap import WMAP

function_dict = {
    "dirac_delta": DiracDelta,
    "earth": Earth,
    "elongated_gaussian": ElongatedGaussian,
    "gaussian": Gaussian,
    "harmonic_gaussian": HarmonicGaussian,
    "identity": Identity,
    "slepian": Slepian,
    "spherical_harmonic": SphericalHarmonic,
    "squashed_gaussian": SquashedGaussian,
    "wmap": WMAP,
}