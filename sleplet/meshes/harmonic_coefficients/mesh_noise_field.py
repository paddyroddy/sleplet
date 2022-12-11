from dataclasses import dataclass, field

from sleplet.meshes.harmonic_coefficients.mesh_field import MeshField
from sleplet.meshes.mesh_harmonic_coefficients import MeshHarmonicCoefficients
from sleplet.utils.noise import compute_snr, create_mesh_noise
from sleplet.utils.string_methods import filename_args


@dataclass
class MeshNoiseField(MeshHarmonicCoefficients):
    SNR: float
    _SNR: float = field(default=10, init=False, repr=False)

    def __post_init__(self) -> None:
        super().__post_init__()

    def _create_coefficients(self) -> None:
        mf = MeshField(self.mesh)
        noise = create_mesh_noise(mf.coefficients, self.SNR)
        compute_snr(mf.coefficients, noise, "Harmonic")
        self.coefficients = noise

    def _create_name(self) -> None:
        self.name = f"{self.mesh.name}_noise_field{filename_args(self.SNR, 'snr')}"

    def _set_reality(self) -> None:
        self.reality = True

    def _set_spin(self) -> None:
        self.spin = 0

    def _setup_args(self) -> None:
        if isinstance(self.extra_args, list):
            num_args = 1
            if len(self.extra_args) != num_args:
                raise ValueError(f"The number of extra arguments should be {num_args}")
            self.SNR = self.extra_args[0]

    @property  # type:ignore
    def SNR(self) -> float:
        return self._SNR

    @SNR.setter
    def SNR(self, SNR: float) -> None:
        if isinstance(SNR, property):
            # initial value not specified, use default
            # https://stackoverflow.com/a/61480946/7359333
            SNR = MeshNoiseField._SNR
        self._SNR = SNR