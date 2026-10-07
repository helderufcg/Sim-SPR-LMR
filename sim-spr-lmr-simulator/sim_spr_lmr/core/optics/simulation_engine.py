"""Execute AIM and WIM optical simulations from normalized domain input.

The module selects prism or fiber propagation, resolves wavelength-dependent
material indices, evaluates multilayer responses, and reports progress while
leaving result metrics to ``post_processing``.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import replace
from functools import lru_cache
import time

import numpy as np
from scipy.optimize import brentq
from scipy.special import j0, j1, k0, k1, jn_zeros

from sim_spr_lmr.core.domain import LayerConfig, SimulationConfig, SimulationResult
from sim_spr_lmr.core.materials import (
    DRUDE_LORENTZ_DISPERSION_MODEL,
    calculate_fiber_core_index,
    calculate_configured_refractive_index,
    normalize_dispersion_model_name,
    supports_dispersion_model,
)
from .post_processing import build_simulation_result
from .transfer_matrix import calculate_reflectance

ProgressCallback = Callable[[int], None]
LogCallback = Callable[[str], None]

LMR_SPR_BATCH_SIZE = 512

# Script-level switch between the ordinary angular power integral and its
# LP01-centered Gaussian-envelope approximation for D-shaped fibers.
D_SHAPED_USE_MODAL_ENVELOPE = False
D_SHAPED_DESIGN_WAVELENGTH_M = 500e-9
# Phenomenological angular width of the modal envelope, in radians.
D_SHAPED_MODAL_SIGMA_RAD = np.deg2rad(0.1)


def _d_shaped_lp01_center_rad(config: SimulationConfig) -> float:
    """Return the fixed effective incidence angle of LP01 at the design wavelength.

    Solve the scalar step-index characteristic equation in the fundamental
    branch, 0 < u < the first zero of J0, with u² + w² = V² and
    b = w² / V². The equivalent ray angle is measured from the interface normal.
    """

    if config.fiber is None:
        raise ValueError("D-shaped modal center requires a fiber configuration.")
    core_index = float(
        np.real(
            _resolve_lmr_spr_core_indices(
                config, np.array([D_SHAPED_DESIGN_WAVELENGTH_M])
            )[0]
        )
    )
    cladding_index = float(
        np.real(
            _calculate_cladding_index(
                core_index=complex(core_index),
                numerical_aperture=config.fiber.numerical_aperture,
                explicit_cladding_index=config.fiber.cladding_index,
            )
        )
    )
    index_difference = core_index**2 - cladding_index**2
    if index_difference <= 0:
        raise ValueError("LP01 requires a core index greater than the cladding index.")
    radius_m = config.fiber.core_diameter_m / 2.0
    v_number = (
        (2.0 * np.pi * radius_m / D_SHAPED_DESIGN_WAVELENGTH_M)
        * np.sqrt(index_difference)
    )
    upper_u = min(v_number, float(jn_zeros(0, 1)[0]))

    def characteristic(u: float) -> float:
        w = np.sqrt(v_number**2 - u**2)
        return u * j1(u) / j0(u) - w * k1(w) / k0(w)

    u = brentq(characteristic, np.finfo(float).eps, np.nextafter(upper_u, 0.0))
    b = 1.0 - (u / v_number) ** 2
    effective_index = np.sqrt(cladding_index**2 + b * index_difference)
    return float(np.arcsin(effective_index / core_index))


# Selects the correct prism/fiber and AIM/WIM execution path for the configuration.
def run_simulation(
    config: SimulationConfig,
    progress_callback: ProgressCallback | None = None,
    log_callback: LogCallback | None = None,
) -> SimulationResult:
    """Run the numerical pipeline and return a complete SimulationResult."""

    started_at = time.perf_counter()

    if config.coupling == "Fiber":
        axis_x, reflectance_curves, critical_points = _run_lmr_spr_fiber_wim(
            config=config,
            progress_callback=progress_callback,
            log_callback=log_callback,
        )
    elif config.simulator == "LMR+SPR" and config.coupling == "Prism":
        axis_x, reflectance_curves, critical_points = _run_wim(
            config=config,
            progress_callback=progress_callback,
            log_callback=log_callback,
        )
    elif config.interrogation_mode == "AIM":
        # AIM varies the incidence angle while keeping wavelength fixed.
        axis_x, reflectance_curves, critical_points = _run_aim(
            config=config,
            progress_callback=progress_callback,
            log_callback=log_callback,
        )
    elif config.interrogation_mode == "WIM":
        # WIM varies the wavelength while keeping angle fixed.
        axis_x, reflectance_curves, critical_points = _run_wim(
            config=config,
            progress_callback=progress_callback,
            log_callback=log_callback,
        )
    else:
        raise ValueError(f"Unsupported interrogation mode: {config.interrogation_mode}")

    runtime_seconds = time.perf_counter() - started_at
    return build_simulation_result(
        config=config,
        axis_x=axis_x,
        reflectance_curves=reflectance_curves,
        runtime_seconds=runtime_seconds,
        critical_points=critical_points,
    )


# Evaluates the angular interrogation response and forwards it to post-processing.
def _run_aim(
    config: SimulationConfig,
    progress_callback: ProgressCallback | None,
    log_callback: LogCallback | None,
) -> tuple[list[float], list[list[float]], list[float]]:
    if config.incidence_wavelength_m is None:
        raise ValueError("AIM simulations require an incidence wavelength.")

    scan_axis_rad = np.arange(config.scan_start, config.scan_stop, config.scan_step)
    axis_x = [float(value * (180 / np.pi)) for value in scan_axis_rad]

    layer_thicknesses = [layer.thickness_m for layer in config.layers]
    analyte_layer_index = _find_analyte_layer_index(config.layers)

    reflectance_curves: list[list[float]] = []
    critical_points: list[float] = []

    # One full curve is generated for each analyte refractive index in the sweep.
    for analyte_index in config.analyte_indices:
        indices_for_analyte = _layer_indices_from_config(config.layers, config.incidence_wavelength_m)
        indices_for_analyte[analyte_layer_index] = analyte_index

        if log_callback is not None:
            log_callback(f"Calculating for the analyte {analyte_index.real} RIU...")

        critical_point_deg = round(abs(np.arcsin(analyte_index / indices_for_analyte[0])) * (180 / np.pi), 3)
        critical_points.append(float(critical_point_deg))

        curve: list[float] = []
        for step, theta_i in enumerate(scan_axis_rad):
            reflectance = _calculate_selected_polarization_reflectance(
                layer_indices=indices_for_analyte,
                layer_thicknesses_m=layer_thicknesses,
                incidence_angle_rad=float(theta_i),
                wavelength_m=config.incidence_wavelength_m,
                polarization=config.polarization,
            )
            curve.append(reflectance)

            if progress_callback is not None:
                progress_callback(int((step + 1) * 100 / len(scan_axis_rad)))

        reflectance_curves.append(curve)

    return axis_x, reflectance_curves, critical_points


# Runs the combined LMR+SPR fiber wavelength-interrogation approximation.
def _run_lmr_spr_fiber_wim(
    config: SimulationConfig,
    progress_callback: ProgressCallback | None,
    log_callback: LogCallback | None,
) -> tuple[list[float], list[list[float]], list[float]]:
    """Run the multimode-fiber WIM pipeline shared by LMR, SPR and LMR+SPR."""

    if config.fiber is None:
        raise ValueError("Optical-fiber simulations require a fiber configuration.")
    if config.interrogation_mode != "WIM":
        raise ValueError("Optical-fiber coupling supports only wavelength interrogation mode.")
    if config.polarization not in {"TM", "TE", "TE+TM"}:
        raise ValueError("Optical-fiber polarization must be TE, TM or TE+TM.")

    # Add half a step so floating-point rounding does not omit the configured
    # upper wavelength from this inclusive spectral grid.
    scan_axis_m = np.arange(
        config.scan_start,
        config.scan_stop + (config.scan_step * 0.5),
        config.scan_step,
    )
    axis_x = [float(value * 1e9) for value in scan_axis_m]
    total_batches = max(
        len(config.analyte_indices) * max(int(np.ceil(len(scan_axis_m) / LMR_SPR_BATCH_SIZE)), 1),
        1,
    )
    completed_batches = 0

    response_curves: list[list[float]] = []

    for analyte_index in config.analyte_indices:
        if log_callback is not None:
            log_callback(f"Calculating fiber spectrum for analyte {analyte_index.real:.4f} RIU...")

        curve = np.empty(len(scan_axis_m), dtype=float)
        for start in range(0, len(scan_axis_m), LMR_SPR_BATCH_SIZE):
            stop = min(start + LMR_SPR_BATCH_SIZE, len(scan_axis_m))
            curve[start:stop] = _transmitted_power_batch_for_selected_polarization(
                config=config,
                wavelengths_m=scan_axis_m[start:stop],
                analyte_index=analyte_index,
            )

            completed_batches += 1
            if progress_callback is not None:
                progress_callback(int(completed_batches * 100 / total_batches))

        response_curves.append(curve.tolist())

    return axis_x, response_curves, []


# Selects TE, TM, or the unpolarized average for batched fiber calculations.
def _transmitted_power_batch_for_selected_polarization(
    config: SimulationConfig,
    wavelengths_m: np.ndarray,
    analyte_index: complex,
) -> np.ndarray:
    """Return the selected fiber transmission, including unpolarized light.

    Each primitive polarization completes its own ``R ** N(theta)`` operation
    and angular integration before the two transmitted-power spectra are
    averaged.  This preserves the physically correct order of operations.
    """

    if config.polarization != "TE+TM":
        return _transmitted_power_batch(config, wavelengths_m, analyte_index)

    te_transmission = _transmitted_power_batch(
        replace(config, polarization="TE"),
        wavelengths_m,
        analyte_index,
    )
    tm_transmission = _transmitted_power_batch(
        replace(config, polarization="TM"),
        wavelengths_m,
        analyte_index,
    )
    return (te_transmission + tm_transmission) / 2.0


# Computes wavelength-batched transmission through the fiber-coupled stack.
def _transmitted_power_batch(
    config: SimulationConfig,
    wavelengths_m: np.ndarray,
    analyte_index: complex,
    *,
    integration_rule: str = "gauss_legendre",
) -> np.ndarray:
    """Return multimode TE or TM transmission for one wavelength batch.

    This is the vectorized transfer-matrix/angular-integration calculation from
    ``teste_SPR+LMR.py``.  Keeping wavelength and angle as array dimensions
    avoids the former Python loop over every wavelength and guided ray.
    """

    if config.fiber is None or config.fiber.core is None:
        raise ValueError("Optical-fiber configuration is incomplete.")

    lam = np.asarray(wavelengths_m, dtype=float)[:, None]
    core_indices = _resolve_lmr_spr_core_indices(config, wavelengths_m)[:, None]
    eps_core = core_indices**2

    cladding_indices = np.asarray(
        [
            _calculate_cladding_index(
                core_index=core_index,
                numerical_aperture=config.fiber.numerical_aperture,
                explicit_cladding_index=config.fiber.cladding_index,
            )
            for core_index in core_indices[:, 0]
        ],
        dtype=complex,
    )[:, None]
    theta_critical = np.arcsin(
        np.clip(np.real(cladding_indices / core_indices), -1.0, 1.0)
    )
    margin = max(float(config.fiber.guiding_margin_rad), 1e-9)
    theta_min = theta_critical + margin
    theta_max = (np.pi / 2) - margin
    is_d_shaped = config.fiber.fiber_type == "d_shaped"
    if is_d_shaped or integration_rule == "gauss_legendre":
        theta, quadrature_weights = _gauss_legendre_grid(
            theta_min,
            theta_max,
            max(config.fiber.angular_samples, 16),
        )
    else:
        angular_coordinate = np.linspace(
            0.0,
            1.0,
            num=max(config.fiber.angular_samples, 16),
        )[None, :]
        theta = theta_min + ((theta_max - theta_min) * angular_coordinate)
        quadrature_weights = None
    sin2 = np.sin(theta) ** 2

    eps_analyte = complex(analyte_index**2)
    if config.polarization == "TM":
        # Keep the admittance expressions explicit because complex square-root
        # branches and division order define the convention used by the matrix stack.
        q_core = np.sqrt(eps_core - (eps_core * sin2) + 0j) / eps_core
        q_analyte = np.sqrt(eps_analyte - (eps_core * sin2) + 0j) / eps_analyte
    elif config.polarization == "TE":
        q_core = np.sqrt(eps_core - (eps_core * sin2) + 0j)
        q_analyte = np.sqrt(eps_analyte - (eps_core * sin2) + 0j)
    else:
        raise ValueError("Optical-fiber polarization must be either TM or TE.")

    matrix_shape = theta.shape
    m11 = np.ones(matrix_shape, dtype=complex)
    m12 = np.zeros(matrix_shape, dtype=complex)
    m21 = np.zeros(matrix_shape, dtype=complex)
    m22 = np.ones(matrix_shape, dtype=complex)

    if is_d_shaped:
        residual_cladding = config.fiber.residual_cladding_thickness_m
        outer_diameter = config.fiber.outer_diameter_m
        if residual_cladding is None or residual_cladding < 0:
            raise ValueError("D-shaped fiber residual cladding must be defined and non-negative.")
        if outer_diameter is None or outer_diameter <= 0:
            raise ValueError("D-shaped fiber outer diameter must be greater than zero.")

        # The residual fluorinated cladding is a finite dispersive layer. Its
        # index is derived from the selected core and NA at every wavelength.
        epsilon_cladding = cladding_indices**2
        root = np.sqrt(epsilon_cladding - (eps_core * sin2) + 0j)
        beta = (2 * np.pi * residual_cladding * root) / lam
        q_layer = root / epsilon_cladding if config.polarization == "TM" else root
        cosine = np.cos(beta)
        sine = np.sin(beta)
        a = cosine
        b = (-1j * sine) / q_layer
        c = -1j * q_layer * sine
        d = cosine
        m11, m12, m21, m22 = (
            (m11 * a) + (m12 * c),
            (m11 * b) + (m12 * d),
            (m21 * a) + (m22 * c),
            (m21 * b) + (m22 * d),
        )

    for layer in config.layers:
        if layer.is_analyte:
            continue
        epsilon_layer = _lmr_spr_layer_permittivity(layer, wavelengths_m)[:, None]
        root = np.sqrt(epsilon_layer - (eps_core * sin2) + 0j)
        beta = (2 * np.pi * layer.thickness_m * root) / lam
        q_layer = root / epsilon_layer if config.polarization == "TM" else root
        cosine = np.cos(beta)
        sine = np.sin(beta)
        a = cosine
        b = (-1j * sine) / q_layer
        c = -1j * q_layer * sine
        d = cosine
        m11, m12, m21, m22 = (
            (m11 * a) + (m12 * c),
            (m11 * b) + (m12 * d),
            (m21 * a) + (m22 * c),
            (m21 * b) + (m22 * d),
        )

    numerator = ((m11 + (m12 * q_analyte)) * q_core) - (m21 + (m22 * q_analyte))
    denominator = ((m11 + (m12 * q_analyte)) * q_core) + (m21 + (m22 * q_analyte))
    reflectance = np.abs(numerator / denominator) ** 2

    if is_d_shaped:
        transverse_distance = 2.0 * (
            (float(config.fiber.outer_diameter_m) / 2.0)
            + (config.fiber.core_diameter_m / 2.0)
            + float(config.fiber.residual_cladding_thickness_m)
        )
        # One interaction advances ``transverse_distance * tan(theta)`` along
        # the sensing region, so their ratio gives the effective reflection count.
        reflection_count = config.fiber.unclad_length_m / (
            transverse_distance * np.tan(theta)
        )
    else:
        reflection_count = config.fiber.unclad_length_m / (
            config.fiber.core_diameter_m * np.tan(theta)
        )
    if config.fiber.power_distribution_model == "uniform":
        weights = np.ones_like(theta, dtype=float)
    else:
        weights = (
            (np.real(core_indices) ** 2 * np.sin(theta) * np.cos(theta))
            / (1 - (np.real(core_indices) ** 2 * np.cos(theta) ** 2)) ** 2
        )
    if is_d_shaped and D_SHAPED_USE_MODAL_ENVELOPE:
        # Effective-angle approximation for the fundamental LP01 mode.
        # The scalar step-index solution gives its propagation constant and
        # hence theta_0 at the 500 nm design wavelength (Gloge, 1971,
        # DOI: 10.1364/AO.10.002252). Keep theta_0 fixed across the scan.
        #
        # Fundamental-mode transverse fields can be approximated by Gaussians
        # (Marcuse, 1978, DOI: 10.1364/JOSA.68.000103; Nemoto and Makimoto,
        # 1979, DOI: 10.1007/BF00619826). This motivates, but does not derive,
        # the narrow angular envelope used in this ray/TMM approximation:
        # G(theta) = exp[-0.5 * ((theta - theta_0) / sigma_theta)^2].
        # sigma_theta = 0.1 deg is a phenomenological numerical broadening,
        # not a physical distribution of guided modes.
        modal_center_rad = _d_shaped_lp01_center_rad(config)
        modal_envelope = np.exp(
            -0.5 * ((theta - modal_center_rad) / D_SHAPED_MODAL_SIGMA_RAD) ** 2
        )
        weights = weights * modal_envelope

    if quadrature_weights is None:
        numerator = _trapezoid(weights * (reflectance**reflection_count), theta, axis=1)
        denominator = _trapezoid(weights, theta, axis=1)
    else:
        numerator = np.sum(
            quadrature_weights * weights * (reflectance**reflection_count),
            axis=1,
        )
        denominator = np.sum(quadrature_weights * weights, axis=1)
    return np.real(numerator / denominator)


def _transmitted_power_batch_tm(
    config: SimulationConfig,
    wavelengths_m: np.ndarray,
    analyte_index: complex,
) -> np.ndarray:
    """Evaluate a TM-only batch with trapezoidal angular integration."""

    if config.polarization != "TM":
        raise ValueError("The TM batch entry point requires TM polarization.")
    return _transmitted_power_batch(
        config,
        wavelengths_m,
        analyte_index,
        integration_rule="legacy_trapezoid",
    )


def _lmr_spr_layer_permittivity(layer: LayerConfig, wavelengths_m: np.ndarray) -> np.ndarray:
    """Resolve fiber-coating permittivity, including fixed ITO and Ag models."""

    material_name = layer.material_name.strip().lower()
    wavelength_um = np.asarray(wavelengths_m, dtype=float) * 1e6

    dispersion_model = normalize_dispersion_model_name(layer.dispersion_model)
    if material_name == "ito" and dispersion_model != DRUDE_LORENTZ_DISPERSION_MODEL:
        # The simple ITO option uses a fixed wavelength-domain Drude
        # parameterization; the alternative branch is resolved by the catalog.
        return _drude_permittivity(wavelength_um, epsilon_inf=3.8, lambda_p_um=0.56497, lambda_c_um=11.21076)
    if material_name in {"ag", "silver"}:
        return _drude_permittivity(
            wavelength_um,
            epsilon_inf=layer.drude_epsilon_inf if layer.dispersion_model == "drude" else 1.0,
            lambda_p_um=layer.drude_lambda_p_um if layer.dispersion_model == "drude" else 0.14541,
            lambda_c_um=layer.drude_lambda_c_um if layer.dispersion_model == "drude" else 17.6140,
        )

    indices = np.asarray(
        [_resolve_wim_refractive_index(layer, float(wavelength)) for wavelength in wavelengths_m],
        dtype=complex,
    )
    return indices**2


def _resolve_lmr_spr_core_indices(config: SimulationConfig, wavelengths_m: np.ndarray) -> np.ndarray:
    """Resolve core indices using the coefficient set defined by each fiber model."""

    if config.fiber is None or config.fiber.core is None:
        raise ValueError("Fiber core configuration is required.")

    core = config.fiber.core
    if config.fiber.fiber_type == "d_shaped":
        # D-shaped fibers use the configured catalog or custom coefficients.
        # Removed-cladding silica uses the rounded constants defined by that model.
        return np.asarray(
            [_resolve_fiber_core_index(config, float(wavelength)) for wavelength in wavelengths_m],
            dtype=complex,
        )
    if not core.use_custom_sellmeier and core.material_name.strip().lower() in {"silic", "silica"}:
        wavelength_um = np.asarray(wavelengths_m, dtype=float) * 1e6
        b1, b2, b3 = 0.69617, 0.40794, 0.89748
        c1, c2, c3 = 4.67915e-3, 1.35121e-2, 97.93400
        index_squared = (
            1
            + ((b1 * wavelength_um**2) / (wavelength_um**2 - c1))
            + ((b2 * wavelength_um**2) / (wavelength_um**2 - c2))
            + ((b3 * wavelength_um**2) / (wavelength_um**2 - c3))
        )
        return np.sqrt(index_squared).astype(complex)

    return np.asarray(
        [_resolve_fiber_core_index(config, float(wavelength)) for wavelength in wavelengths_m],
        dtype=complex,
    )


def _drude_permittivity(
    wavelength_um: np.ndarray,
    *,
    epsilon_inf: float,
    lambda_p_um: float | None,
    lambda_c_um: float | None,
) -> np.ndarray:
    if lambda_p_um is None or lambda_c_um is None:
        raise ValueError("Fiber-coating Drude parameters must be defined.")
    return epsilon_inf - ((wavelength_um**2 * lambda_c_um) / (lambda_p_um**2 * (lambda_c_um + (1j * wavelength_um))))


@lru_cache(maxsize=None)
def _gauss_legendre_rule(num_samples: int) -> tuple[np.ndarray, np.ndarray]:
    """Return cached Gauss-Legendre nodes and weights on [-1, 1]."""

    return np.polynomial.legendre.leggauss(num_samples)


def _gauss_legendre_grid(
    lower_bound: float | np.ndarray,
    upper_bound: float | np.ndarray,
    num_samples: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Transform a Gauss-Legendre rule to one or many angular intervals."""

    nodes, weights = _gauss_legendre_rule(num_samples)
    midpoint = (lower_bound + upper_bound) / 2
    half_range = (upper_bound - lower_bound) / 2
    return midpoint + (half_range * nodes), half_range * weights


def _trapezoid(values: np.ndarray, coordinates: np.ndarray, axis: int) -> np.ndarray:
    """Integrate samples along their explicit coordinates with a trapezoidal rule."""

    if hasattr(np, "trapezoid"):
        return np.trapezoid(values, x=coordinates, axis=axis)
    return np.trapz(values, x=coordinates, axis=axis)


# Evaluates the wavelength interrogation response for prism or fiber coupling.
def _run_wim(
    config: SimulationConfig,
    progress_callback: ProgressCallback | None,
    log_callback: LogCallback | None,
) -> tuple[list[float], list[list[float]], list[float]]:
    if config.incidence_angle_rad is None:
        raise ValueError("WIM simulations require an incidence angle.")

    if config.simulator == "LMR+SPR" and config.coupling == "Prism":
        scan_axis_m = np.arange(
            config.scan_start,
            config.scan_stop + (0.5 * config.scan_step),
            config.scan_step,
        )
    else:
        scan_axis_m = np.arange(config.scan_start, config.scan_stop, config.scan_step)
    axis_x = [float(value * 1E9) for value in scan_axis_m]

    layer_thicknesses = [layer.thickness_m for layer in config.layers]
    if config.response_quantity == "reflectance_db":
        # Prism and analyte are semi-infinite. Their UI thicknesses are only
        # table placeholders and must not contribute propagation phases.
        layer_thicknesses[0] = 0.0
        layer_thicknesses[-1] = 0.0
    analyte_layer_index = _find_analyte_layer_index(config.layers)

    reflectance_curves: list[list[float]] = []

    # In WIM the material model may change with wavelength, so the full layer
    # index vector is rebuilt at every scan point.
    for analyte_index in config.analyte_indices:
        if log_callback is not None:
            log_callback(f"Calculating for the analyte {analyte_index.real} RIU...")

        curve: list[float] = []
        for step, wavelength in enumerate(scan_axis_m):
            indices_for_wavelength = []
            for layer_index, layer in enumerate(config.layers):
                if layer_index == analyte_layer_index:
                    indices_for_wavelength.append(analyte_index)
                else:
                    indices_for_wavelength.append(_resolve_wim_refractive_index(layer, float(wavelength)))

            reflectance = _calculate_selected_polarization_reflectance(
                layer_indices=indices_for_wavelength,
                layer_thicknesses_m=layer_thicknesses,
                incidence_angle_rad=config.incidence_angle_rad,
                wavelength_m=float(wavelength),
                polarization=config.polarization,
            )
            if config.response_quantity == "reflectance_db":
                reflectance = float(10.0 * np.log10(max(reflectance, 1e-12)))
            curve.append(reflectance)

            if progress_callback is not None:
                progress_callback(int((step + 1) * 100 / len(scan_axis_m)))

        reflectance_curves.append(curve)

    return axis_x, reflectance_curves, []


# Computes reflectance for one wavelength using the requested polarization mode.
def _calculate_selected_polarization_reflectance(
    *,
    layer_indices: Sequence[complex],
    layer_thicknesses_m: Sequence[float],
    incidence_angle_rad: float,
    wavelength_m: float,
    polarization: str,
) -> float:
    """Calculate TE, TM, or equal-power unpolarized reflectance."""

    if polarization != "TE+TM":
        return calculate_reflectance(
            layer_indices=layer_indices,
            layer_thicknesses_m=layer_thicknesses_m,
            incidence_angle_rad=incidence_angle_rad,
            wavelength_m=wavelength_m,
            polarization=polarization,
        )

    reflectance_te = calculate_reflectance(
        layer_indices=layer_indices,
        layer_thicknesses_m=layer_thicknesses_m,
        incidence_angle_rad=incidence_angle_rad,
        wavelength_m=wavelength_m,
        polarization="TE",
    )
    reflectance_tm = calculate_reflectance(
        layer_indices=layer_indices,
        layer_thicknesses_m=layer_thicknesses_m,
        incidence_angle_rad=incidence_angle_rad,
        wavelength_m=wavelength_m,
        polarization="TM",
    )
    return (reflectance_te + reflectance_tm) / 2.0


def _resolve_wim_refractive_index(layer: LayerConfig, wavelength_m: float) -> complex:
    if supports_dispersion_model(layer.material_id):
        return _resolve_layer_refractive_index(layer, wavelength_m)
    if layer.refractive_index is None:
        raise ValueError(f"Layer '{layer.material_name}' is missing a refractive index.")
    return layer.refractive_index


def _resolve_fiber_core_index(config: SimulationConfig, wavelength_m: float) -> complex:
    if config.fiber is None or config.fiber.core is None:
        raise ValueError("Fiber core configuration is required.")
    return calculate_fiber_core_index(config.fiber.core, wavelength_m)


def _calculate_cladding_index(
    core_index: complex,
    numerical_aperture: float | None,
    explicit_cladding_index: complex | None = None,
) -> complex:
    if explicit_cladding_index is not None:
        return explicit_cladding_index

    if numerical_aperture is None or numerical_aperture <= 0:
        raise ValueError(
            "Fiber cladding index could not be resolved. Provide a positive numerical aperture "
            "or an explicit cladding index in the fiber configuration."
        )

    core_real = float(np.real(core_index))
    cladding_real = np.sqrt(max((core_real**2) - (numerical_aperture**2), 1e-12))
    return complex(cladding_real, 0.0)


def _find_analyte_layer_index(layers: Sequence[LayerConfig]) -> int:
    for index, layer in enumerate(layers):
        if layer.is_analyte:
            return index
    raise ValueError("No analyte layer found in the simulation configuration.")


def _layer_indices_from_config(layers: Sequence[LayerConfig], wavelength_m: float) -> list[complex]:
    indices: list[complex] = []
    for layer in layers:
        if supports_dispersion_model(layer.material_id):
            indices.append(_resolve_layer_refractive_index(layer, wavelength_m))
        elif layer.refractive_index is not None:
            indices.append(layer.refractive_index)
        else:
            raise ValueError(f"Layer '{layer.material_name}' is missing a refractive index.")
    return indices


# Resolves each layer index at the wavelength currently being simulated.
def _resolve_layer_refractive_index(layer: LayerConfig, wavelength_m: float) -> complex:
    return calculate_configured_refractive_index(
        layer.material_id,
        wavelength_m,
        material_name=layer.material_name,
        dispersion_model=layer.dispersion_model,
        drude_lambda_p_um=layer.drude_lambda_p_um,
        drude_lambda_c_um=layer.drude_lambda_c_um,
        drude_epsilon_inf=layer.drude_epsilon_inf,
    )
