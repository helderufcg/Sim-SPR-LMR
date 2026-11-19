# Tests

This directory contains the automated test suite for Sim-SPR / Sim-LMR / Sim-SPR+LMR. The tests use `pytest` as the test runner, while most test cases are organized with Python's `unittest` classes and assertions.

### Core numerical and physical behavior

The [`core/`](core/) subdirectory tests the domain and optical calculations:

- Material catalog identifiers, refractive-index models, and dispersion options.
- Transfer-matrix reflectance calculations for TE, TM, and unpolarized polarization.
- Resonance position, FWHM, sensitivity, and figure-of-merit post-processing.
- Automatic resonance detection and resonance-track association.
- SPR, LMR, and combined SPR+LMR reference pipelines, including D-Profile fibers.
- Reflectance response-scale conversion and related plot/export labels.

### Application and presentation behavior

The tests in the root of this directory cover application workflows and the Qt presentation layer:

- Fiber navigation, fiber compatibility, and fiber-specific validation.
- Material options exposed by the generated Qt interface.
- External-file analysis UI structure and generated UI consistency.
- Parametric-analysis input controls, worker execution, result rendering, and exports.
- Parametric-analysis service behavior for thickness and incidence-angle sweeps.

### Preview utilities

`previews/parametric_analysis_preview.py` opens the real parametric-analysis window with deterministic synthetic data. It is intended for visual inspection of the graphs and UI layout, not for automated assertions.

## Requirements

- Python 3.10 or newer.
- Project dependencies from the repository-level `requirements.txt`.
- `pytest` for running the test suite.
- A Qt-compatible environment for UI tests. The parametric-analysis UI tests use
  `QT_QPA_PLATFORM=offscreen`, so they do not require a visible desktop window.

Install the dependencies from the repository root:

```bash
python -m pip install -r requirements.txt
python -m pip install pytest
```

## Running the tests

Run the complete suite from the repository root:

```bash
python -m pytest
```

Run only the core tests:

```bash
python -m pytest tests/core
```

Run a specific test module or test case:

```bash
python -m pytest tests/test_parametric_analysis_service.py
python -m pytest tests/test_parametric_analysis_service.py -k thickness
```

Use verbose output when investigating a failure:

```bash
python -m pytest -vv
```

## Test categories at a glance

| Location | Main responsibility |
| --- | --- |
| `tests/core/test_materials.py` | Material catalog and dispersion models |
| `tests/core/test_transfer_matrix.py` | Fresnel and transfer-matrix calculations |
| `tests/core/test_post_processing.py` | Resonance metrics and derived quantities |
| `tests/core/test_resonance_tracking.py` | Multi-step resonance association |
| `tests/core/test_lmr_spr_reference_pipeline.py` | SPR+LMR reference scenarios |
| `tests/core/test_response_scale.py` | Linear/dB response presentation and export |
| `tests/test_fiber_compatibility.py` | Fiber navigation, mapping, and validation |
| `tests/test_material_catalog_ui.py` | Material and polarization options in the UI |
| `tests/test_parametric_analysis_service.py` | Parametric sweep calculations |
| `tests/test_parametric_analysis_ui.py` | Parametric-analysis window behavior |
| `tests/test_parametric_analysis_exporter.py` | Parametric-analysis export files |
| `tests/test_external_file_analysis_ui.py` | External-file analysis UI structure |

