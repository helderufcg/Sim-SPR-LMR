"""Material dispersion models used by the optical simulation core.

The helpers exported here resolve refractive indices independently from the UI.
"""

from .dispersion_models import (
    DRUDE_DISPERSION_MODEL,
    DRUDE_LORENTZ_DISPERSION_MODEL,
    EXPERIMENTAL_DISPERSION_MODEL,
    FILMETRICS_EXPERIMENTAL_DISPERSION_MODEL,
    calculate_copper_filmetrics_refractive_index,
    calculate_fiber_core_index,
    calculate_configured_refractive_index,
    calculate_drude_refractive_index,
    calculate_drude_lorentz_refractive_index,
    calculate_refractive_index,
    calculate_sellmeier_refractive_index,
    calculate_silicon_refractive_index,
    default_drude_parameters_for_material,
    material_supports_drude_override,
    material_supports_drude_lorentz,
    material_supports_filmetrics_experimental,
    material_uses_builtin_drude,
    material_uses_builtin_drude_lorentz,
    normalize_dispersion_model_name,
    resolve_material_id,
    supports_dispersion_model,
)

__all__ = [
    "DRUDE_DISPERSION_MODEL",
    "DRUDE_LORENTZ_DISPERSION_MODEL",
    "EXPERIMENTAL_DISPERSION_MODEL",
    "FILMETRICS_EXPERIMENTAL_DISPERSION_MODEL",
    "calculate_copper_filmetrics_refractive_index",
    "calculate_fiber_core_index",
    "calculate_configured_refractive_index",
    "calculate_drude_refractive_index",
    "calculate_drude_lorentz_refractive_index",
    "calculate_refractive_index",
    "calculate_sellmeier_refractive_index",
    "calculate_silicon_refractive_index",
    "default_drude_parameters_for_material",
    "material_supports_drude_override",
    "material_supports_drude_lorentz",
    "material_supports_filmetrics_experimental",
    "material_uses_builtin_drude",
    "material_uses_builtin_drude_lorentz",
    "normalize_dispersion_model_name",
    "resolve_material_id",
    "supports_dispersion_model",
]
