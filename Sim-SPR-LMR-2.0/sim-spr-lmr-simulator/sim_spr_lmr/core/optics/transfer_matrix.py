"""Transfer-matrix implementation used by the simulation core."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np


# Builds the multilayer transfer matrix and returns the selected polarization reflectance.
def calculate_reflectance(
    layer_indices: Sequence[complex],
    layer_thicknesses_m: Sequence[float],
    incidence_angle_rad: float,
    wavelength_m: float,
    polarization: str,
) -> float:
    """Return reflectance for a multilayer stack using the transfer-matrix method."""

    if len(layer_indices) != len(layer_thicknesses_m):
        raise ValueError("Layer indices and thicknesses must have the same length.")
    if len(layer_indices) < 2:
        raise ValueError("At least two layers are required to calculate reflectance.")
    if polarization not in {"TM", "TE"}:
        raise ValueError("Polarization must be either 'TM' or 'TE'.")

    # Each layer contributes a phase shift and an optical admittance. Those
    # per-layer quantities are then assembled into the global transfer matrix.
    j = complex(0, 1)
    k0 = (2 * np.pi) / wavelength_m

    phase_shifts: list[complex] = []
    admittances: list[complex] = []
    transfer_matrices: list[np.ndarray] = []

    first_index = layer_indices[0]

    for layer, layer_index in enumerate(layer_indices):
        propagation_term = np.sqrt((layer_index**2) - ((first_index * np.sin(incidence_angle_rad)) ** 2))
        phase_shift = k0 * layer_thicknesses_m[layer] * propagation_term

        phase_shifts.append(phase_shift)

        if polarization == "TM":
            admittance = propagation_term / (layer_index**2)
        else:
            admittance = propagation_term

        admittances.append(admittance)

        if layer < (len(layer_indices) - 1):
            transfer_matrices.append(
                np.array(
                    [
                        [np.cos(phase_shift), (-j / admittance) * np.sin(phase_shift)],
                        [-j * admittance * np.sin(phase_shift), np.cos(phase_shift)],
                    ],
                    dtype=complex,
                )
            )

    # Multiply the per-layer matrices in order to obtain the response of the
    # full multilayer stack.
    total_transfer_matrix = transfer_matrices[0]
    for matrix in transfer_matrices[1:]:
        total_transfer_matrix = total_transfer_matrix @ matrix

    first_admittance = admittances[0]
    last_admittance = admittances[-1]

    numerator = (
        (total_transfer_matrix[0][0] + total_transfer_matrix[0][1] * last_admittance) * first_admittance
        - (total_transfer_matrix[1][0] + total_transfer_matrix[1][1] * last_admittance)
    )
    denominator = (
        (total_transfer_matrix[0][0] + total_transfer_matrix[0][1] * last_admittance) * first_admittance
        + (total_transfer_matrix[1][0] + total_transfer_matrix[1][1] * last_admittance)
    )

    # The squared magnitude of the Fresnel reflection coefficient is the
    # reflectance returned to the rest of the pipeline.
    reflection_coefficient = numerator / denominator
    return float(abs(reflection_coefficient) ** 2)
