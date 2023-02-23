import numpy as np
import pytest
from numpy.testing import assert_allclose

from sleplet.utils.harmonic_methods import mesh_forward, mesh_inverse
from sleplet.utils.integration_methods import integrate_whole_mesh


def test_inverse_forward_transform_recovery(mesh_field_region) -> None:
    """
    tests that a given function is recovered after an
    inverse and forward transform on the mesh
    """
    u = mesh_inverse(mesh_field_region.mesh, mesh_field_region.coefficients)
    kernel_recov = mesh_forward(mesh_field_region.mesh, u)
    assert_allclose(
        np.abs(mesh_field_region.coefficients - kernel_recov).mean(), 0, atol=1e-14
    )


@pytest.mark.slow
def test_orthonormality_over_mesh_full(mesh) -> None:
    """
    for the computation of the Slepian D matrix the basis
    functions must be orthornomal over the whole mesh
    """
    orthonormality = np.zeros(
        (mesh.mesh_eigenvalues.shape[0], mesh.mesh_eigenvalues.shape[0])
    )
    for i, phi_i in enumerate(mesh.basis_functions):
        for j, phi_j in enumerate(mesh.basis_functions):
            orthonormality[i, j] = integrate_whole_mesh(
                mesh.vertices, mesh.faces, phi_i, phi_j
            )
    identity = np.identity(mesh.mesh_eigenvalues.shape[0])
    np.testing.assert_allclose(np.abs(orthonormality - identity).mean(), 0, atol=1e-16)