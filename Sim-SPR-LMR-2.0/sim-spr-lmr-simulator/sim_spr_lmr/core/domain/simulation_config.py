"""Pure input models consumed by the simulation core."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
# Describes one optical layer and its optional dispersion configuration.
class LayerConfig:
    """Describes one optical layer used by the simulation core."""

    material_name: str
    material_id: int
    thickness_m: float
    refractive_index: complex | None = None
    description: str = ""
    is_analyte: bool = False
    dispersion_model: str = "experimental"
    drude_lambda_p_um: float | None = None
    drude_lambda_c_um: float | None = None
    drude_epsilon_inf: float = 1.0


@dataclass(slots=True)
# Stores the coefficients used to resolve wavelength-dependent fiber indices.
class SellmeierCoefficients:
    """Sellmeier coefficients for fiber-core refractive-index resolution.

    The Qt screen labels them as A1/A2/A3 and B1/B2/B3, while the core keeps a
    more explicit naming aligned with the equation already.
    """

    b1: float
    b2: float
    b3: float
    c1: float
    c2: float
    c3: float


@dataclass(slots=True)
# Defines how the refractive index of a fiber core is obtained.
class FiberCoreConfig:
    """Describes how the multimode-fiber core index must be resolved."""

    material_name: str
    material_id: int | None = None
    use_custom_sellmeier: bool = False
    sellmeier: SellmeierCoefficients | None = None


@dataclass(slots=True)
# Groups the geometric and material properties of an optical fiber.
class FiberConfig:
    """Parameters specific to the multimode-fiber sensing geometry.

    Mandatory in every multimode-fiber flow:
    - `fiber_type`
    - `unclad_length_m`
    - `core_diameter_m`
    - `core`
    - either `numerical_aperture` or `cladding_index`

    Optional and already generalized in the core:
    - `angular_samples`
    - `power_distribution_model`
    - `cladding_index`
    - `guiding_margin_rad`

    Parameters that may require physical revalidation when changed from the
    base case:
    - `core` material or Sellmeier coefficients
    - `power_distribution_model`
    - explicit `cladding_index`
    """

    fiber_type: str
    unclad_length_m: float
    core_diameter_m: float
    numerical_aperture: float | None = None
    angular_samples: int = 300
    power_distribution_model: str = "uniform"
    cladding_index: complex | None = None
    guiding_margin_rad: float = 1e-5
    core: FiberCoreConfig | None = None
    outer_diameter_m: float | None = None
    residual_cladding_thickness_m: float | None = None


@dataclass(slots=True)
# Aggregates all normalized inputs required by the optical simulation.
class SimulationConfig:
    """Normalized simulation input independent from the Qt widgets.

    Every value here should already be converted to core-friendly units, so the
    numerical engine does not need to understand combo-box indices or UI text.
    """

    simulator: str
    coupling: str
    interrogation_mode: str
    polarization: str
    layers: list[LayerConfig] = field(default_factory=list)
    analyte_indices: list[complex] = field(default_factory=list)
    incidence_wavelength_m: float | None = None
    incidence_angle_rad: float | None = None
    scan_start: float = 0.0
    scan_stop: float = 0.0
    scan_step: float = 0.0
    fiber: FiberConfig | None = None
    response_quantity: str = "reflectance"
    resonance_strategy: str = "single_dip"
    expected_resonance_labels: tuple[str, ...] = ("resonance",)
    resonance_windows_nm: dict[str, tuple[float, float]] = field(default_factory=dict)
    resonance_sort_mode: str = "axis"
    max_tracked_resonances: int = 1
    resonance_depth_threshold_ratio: float = 0.85
    validation_notes: list[str] = field(default_factory=list)
