"""Global Help Center dialog for the simulator UI."""

from __future__ import annotations

from PyQt5 import QtGui, QtWidgets


HELP_TOPICS = [
    {
        "title": "Overview",
        "keywords": "overview purpose spr lmr transfer matrix assumptions scope",
        "summary": "What the simulator calculates and the assumptions behind the model.",
        "body": """
            <h2>Overview</h2>
            <p>Sim-SPR/LMR calculates the optical response of multilayer
            refractive-index sensors. Build a stack, vary the analyte index,
            and simulate SPR, LMR, or combined LMR+SPR resonances.</p>
            <p>Use prism or multimode-fiber coupling. Use AIM to scan incidence
            angle at a fixed wavelength. Use WIM to scan wavelength. Results
            include reflectance or normalized transmission, resonance position,
            sensitivity, FWHM, and figure of merit.</p>
            <p class="warning"><b>Model assumptions:</b> The solver uses the
            transfer-matrix method with homogeneous, planar, isotropic layers.
            It does not model roughness, scattering, temperature, or fabrication
            tolerances unless their effect is included in the entered optical
            constants. Material models are valid only over the ranges supported
            by their cited data.</p>
        """,
    },
    {
        "title": "Quick Start",
        "keywords": "quick start first example spr gold bk7 run",
        "summary": "Run a basic prism-coupled SPR example in eight steps.",
        "body": """
            <h2>Quick Start</h2>
            <ol>
                <li>Select <b>SPR</b>.</li>
                <li>Select <b>Prism</b> coupling and <b>AIM</b>.</li>
                <li>Enter an incident wavelength of <b>633 nm</b>. Select
                <b>TM</b> polarization when the option is shown.</li>
                <li>Add <b>BK7</b> as the first layer. This is the prism.</li>
                <li>Add <b>Gold (Au)</b> with a thickness of <b>50 nm</b>.</li>
                <li>Add the analyte last. Enter <b>1.33 RIU</b>, <b>2</b>
                samples, and a <b>0.01 RIU</b> step.</li>
                <li>Set the angular range to <b>60–89°</b>.</li>
                <li>Click <b>Run</b>. Inspect the reflectance minimum and the
                reported resonance angle.</li>
            </ol>
            <p class="warning"><b>Important:</b> Layer order follows the light
            path. For prism coupling, use prism → coating(s) → analyte.</p>
        """,
    },
    {
        "title": "Main Workflow",
        "keywords": "workflow simulation coupling interrogation stack analyte run results parametric",
        "summary": "Build and check a typical simulation case.",
        "body": """
            <h2>Main Workflow</h2>
            <ol>
                <li><b>Choose the resonance.</b> Select SPR, LMR, or LMR+SPR.</li>
                <li><b>Choose the coupling.</b> Select Prism or Optical Fiber.</li>
                <li><b>Choose the scan.</b> AIM scans angle. WIM scans wavelength.
                LMR+SPR and fiber workflows use WIM.</li>
                <li><b>Configure the source.</b> Enter the fixed wavelength or
                angle and choose the available polarization.</li>
                <li><b>Build the structure.</b> For prism coupling, add the prism
                first. Then add finite coatings. For fiber coupling, configure
                the core and add the coatings. Add one analyte last.</li>
                <li><b>Define the analyte sweep.</b> Enter the initial index,
                number of samples, and positive RIU step.</li>
                <li><b>Set the scan range.</b> Make the final value greater than
                the initial value and include the expected resonance.</li>
                <li><b>Run and review.</b> Confirm the dip, resonance position,
                FWHM, sensitivity, and FOM. Save the layer preset or export the
                results when needed.</li>
            </ol>
            <p>After a conventional run, open <b>Parametric analysis</b> to vary
            one finite-layer thickness or the prism-WIM incidence angle. Use no
            more than 500 sweep points.</p>
        """,
    },
    {
        "title": "Parameters and Options",
        "keywords": "parameters typical values materials dispersion model reference doi thickness angle wavelength fiber",
        "summary": "Main controls, typical values, and the complete material catalog.",
        "body": """
            <h2>Parameters and Options</h2>
            <table>
                <tr><th>Field</th><th>Typical value</th><th>Effect</th></tr>
                <tr><td>Simulation</td><td>SPR, LMR, LMR+SPR</td><td>Selects the resonance family and compatible workflow.</td></tr>
                <tr><td>Polarization</td><td>TM for SPR; TE or TM for LMR</td><td>Changes which optical modes can be excited. TE+TM averages both responses.</td></tr>
                <tr><td>Incident wavelength</td><td>532, 633, or 670 nm</td><td>Fixed in AIM. It changes material indices and resonance position.</td></tr>
                <tr><td>AIM range</td><td>60–89°</td><td>Scans incidence angle with an internal 0.001° step.</td></tr>
                <tr><td>WIM range</td><td>400–1000 nm</td><td>Scans wavelength with an internal 0.1 nm step.</td></tr>
                <tr><td>Layer thickness</td><td>10–100 nm for many metal films</td><td>Changes coupling strength, dip depth, width, and position. Use literature or measured values.</td></tr>
                <tr><td>Analyte index</td><td>1.33 RIU</td><td>Sets the first surrounding-medium index. Accepted range: 1–5 RIU.</td></tr>
                <tr><td>Analyte samples</td><td>2</td><td>Creates multiple curves. At least two are required.</td></tr>
                <tr><td>Analyte step</td><td>0.01 RIU</td><td>Controls the index difference used for sensitivity.</td></tr>
                <tr><td>Fiber geometry</td><td>Use the fiber datasheet</td><td>Detection length is in mm, core diameter in &micro;m, and NA is dimensionless.</td></tr>
            </table>
            <p class="warning"><b>Units:</b> Enter wavelength and coating
            thickness in nm, angles in degrees, fiber length in mm, core diameter
            in &micro;m, and refractive index in RIU.</p>

            <h3>Predefined materials and models</h3>
            <p>The full predefined material catalog is:</p>
            <ul>
                <li><b>Optical glasses and dielectrics:</b> BK7, Silica, N-F2,
                Synthetic sapphire (Al2O3), SF10, FK51A, N-SF14, Acrylic SUVT,
                PVA, Glycerin, Quartz, SF11, CaF2, LiF, and Cytop.</li>
                <li><b>Metals:</b> Gold (Au), Silver (Ag), Copper (Cu), Aluminum
                (Al), Nickel (Ni), and Chromium.</li>
                <li><b>Functional materials:</b> ITO, TiO2, ZnO, Silicon,
                Doped SWCNT, FTO, P3HT:PC61BM, PEDOT:PSS, and 2D HOIP.</li>
                <li><b>Surrounding media:</b> Water and Air.</li>
                <li><b>Fiber-core materials:</b> Silica and PMMA.</li>
                <li><b>Custom material:</b> user-defined complex index.</li>
            </ul>
            <p>The model and reference used for each material are:</p>
            <table>
                <tr><th>Material(s)</th><th>Implemented model</th><th>Reference</th></tr>
                <tr><td>BK7, Silica, N-F2, Synthetic sapphire (Al2O3), SF10, FK51A, N-SF14, Acrylic SUVT, LiF, CaF2</td><td>Sellmeier equation with catalog coefficients</td><td><a href="https://doi.org/10.1038/s41597-023-02898-2">Polyanskiy (2024)</a>; <a href="https://refractiveindex.info/">RefractiveIndex.INFO</a></td></tr>
                <tr><td>SF11</td><td>Sellmeier equation with SCHOTT coefficients</td><td><a href="https://refractiveindex.info/?shelf=specs&amp;book=SCHOTT-optical&amp;page=SF11">SCHOTT/RefractiveIndex.INFO</a>; <a href="https://doi.org/10.1038/s41597-023-02898-2">Polyanskiy (2024)</a></td></tr>
                <tr><td>PMMA (fiber core only)</td><td>Sellmeier equation with catalog coefficients</td><td><a href="https://doi.org/10.1038/s41597-023-02898-2">Polyanskiy (2024)</a>; <a href="https://refractiveindex.info/">RefractiveIndex.INFO</a></td></tr>
                <tr><td>PVA, Glycerin</td><td>Three-term Cauchy equation</td><td><a href="https://doi.org/10.1038/s41597-023-02898-2">Polyanskiy (2024)</a>; <a href="https://refractiveindex.info/">RefractiveIndex.INFO</a></td></tr>
                <tr><td>Quartz</td><td>Wavelength/inverse-wavelength polynomial</td><td><a href="https://doi.org/10.1038/s41597-023-02898-2">Polyanskiy (2024)</a>; <a href="https://refractiveindex.info/">RefractiveIndex.INFO</a></td></tr>
                <tr><td>Gold (Au), Silver (Ag)</td><td>Interpolated experimental complex index; optional Drude model</td><td><a href="https://doi.org/10.1103/PhysRevB.6.4370">Johnson and Christy (1972)</a>; <a href="https://doi.org/10.1063/1.2721779">Sharma and Gupta (2007)</a></td></tr>
                <tr><td>Copper (Cu)</td><td>Interpolated experimental complex index; optional Drude model; alternative experimental table</td><td><a href="https://doi.org/10.1103/PhysRevB.6.4370">Johnson and Christy (1972)</a>; <a href="https://doi.org/10.1063/1.2721779">Sharma and Gupta (2007)</a>; <a href="https://www.kla.com/products/instruments/refractive-index-database/cu/copper">KLA/Filmetrics</a></td></tr>
                <tr><td>Aluminum (Al)</td><td>Drude model</td><td><a href="https://doi.org/10.1063/1.2721779">Sharma and Gupta (2007)</a></td></tr>
                <tr><td>Nickel (Ni)</td><td>Drude model</td><td><a href="https://doi.org/10.1007/s11082-023-05419-y">Kumar et al. (2023)</a></td></tr>
                <tr><td>Chromium</td><td>Drude critical-point model</td><td><a href="https://doi.org/10.1088/0022-3727/40/22/043">Vial and Laroche (2007)</a></td></tr>
                <tr><td>P3HT:PC61BM, PEDOT:PSS, 2D HOIP</td><td>Interpolated tabulated complex optical constants</td><td><a href="https://doi.org/10.1016/j.physb.2022.414048">Yadollahzadeh et al. (2022)</a>; <a href="https://refractiveindex.info/">RefractiveIndex.INFO</a></td></tr>
                <tr><td>TiO2</td><td>Lorentz oscillator model</td><td><a href="https://doi.org/10.1364/OE.466170">Zhang et al. (2022)</a></td></tr>
                <tr><td>ZnO</td><td>Drude model; optional Drude–Lorentz model</td><td><a href="https://doi.org/10.1109/JSEN.2019.2946760">Saini et al. (2020)</a>; Usha and Gupta (2017)</td></tr>
                <tr><td>ITO</td><td>Drude model; optional Drude–Lorentz model</td><td>Mishra, Mishra and Gupta (2015), <a href="https://doi.org/10.1016/j.optcom.2015.01.043">DOI</a>; <a href="https://doi.org/10.1109/JLT.2010.2082492">Del Villar et al. (2010)</a>; <a href="https://doi.org/10.1016/S0040-6090(98)00861-X">Laux et al. (1998)</a></td></tr>
                <tr><td>Silicon</td><td>Wavelength-dependent exponential model</td><td>Mishra et al. (2016); <a href="https://doi.org/10.1364/AO.50.002032">Bhatia and Gupta (2011)</a></td></tr>
                <tr><td>Doped SWCNT</td><td>Drude–Lorentz model</td><td>Mishra et al. (2016); <a href="https://doi.org/10.1103/PhysRevLett.114.176807">Igarashi et al. (2015)</a>; <a href="https://doi.org/10.1016/S0038-1098(98)00614-0">Pichler et al. (1999)</a></td></tr>
                <tr><td>FTO</td><td>Embedded corrected Lorentz–Drude model</td><td><a href="https://github.com/AdeilsonLeal1/Simulador-SPR-LMR">Sim-SPR/LMR source code</a>; external provenance is not recorded</td></tr>
                <tr><td>Cytop</td><td>Constant index, n = 1.34, over 0.2–2.0 &micro;m</td><td><a href="https://www.agc-chemicals.com/jp/en/fluorine/products/cytop/download/index.html">AGC Chemicals</a></td></tr>
                <tr><td>Water</td><td>Fixed index, n = 1.33</td><td><a href="https://github.com/AdeilsonLeal1/Simulador-SPR-LMR">Sim-SPR/LMR source code</a></td></tr>
                <tr><td>Air</td><td>Fixed index, n = 1.0000</td><td><a href="https://github.com/AdeilsonLeal1/Simulador-SPR-LMR">Sim-SPR/LMR source code</a></td></tr>
                <tr><td>Custom material</td><td>User-defined, wavelength-invariant complex index</td><td>No external dataset is applied</td></tr>
            </table>
            <p class="warning"><b>Validity warning:</b> Do not extrapolate a
            tabulated or fitted model beyond its documented wavelength range
            without independent validation. Check custom coefficients and the
            sign convention of the complex refractive index.</p>
        """,
    },
    {
        "title": "Data Input and Output",
        "keywords": "input output formats units csv txt xlsx latex export results graphs resonance sensitivity fwhm fom",
        "summary": "Accepted formats, units, exports, and result interpretation.",
        "body": """
            <h2>Data Input and Output</h2>
            <h3>Input</h3>
            <ul>
                <li>Enter geometry and optical data in the interface.</li>
                <li>Save and load layer presets to reuse a structure.</li>
                <li>For external curve analysis, load one or two CSV/TXT files.
                Put the horizontal axis in column 1 and the response in column 2.</li>
                <li>When comparing two external curves, enter their analyte-index
                difference in RIU.</li>
            </ul>
            <h3>Output</h3>
            <ul>
                <li>Prism workflows show reflectance. Fiber workflows show
                normalized transmission.</li>
                <li>LMR+SPR prism results start in dB. The Scale control can show
                linear R. Resonance detection and FWHM still use the original dB curve.</li>
                <li>Resonance position is reported in degrees for AIM and nm for WIM.</li>
                <li>Sensitivity is reported in deg/RIU for AIM and nm/RIU for WIM.</li>
                <li>FWHM uses the horizontal-axis unit. FOM is sensitivity/FWHM.</li>
                <li>Export the layer table as LaTeX, XLSX, CSV, or TXT. Export
                simulation curves and summaries as TXT. Parametric analysis
                exports metrics and spectra as paired CSV files.</li>
            </ul>
            <p class="warning"><b>Check the result:</b> Confirm that each dip is
            fully inside the scan range before using sensitivity, FWHM, or FOM.
            A clipped dip produces unreliable metrics.</p>
        """,
    },
    {
        "title": "Troubleshooting",
        "keywords": "troubleshooting convergence mesh units error invalid no resonance flat curve import",
        "summary": "Fix common configuration, range, unit, and result problems.",
        "body": """
            <h2>Troubleshooting</h2>
            <ol>
                <li><b>The simulation does not start.</b> Read the validation
                message. Select a simulator, compatible coupling and scan, add
                the required layers, and add exactly one analyte last.</li>
                <li><b>No resonance appears.</b> Widen the scan range. Check layer
                order, polarization, thickness, material choice, and analyte index.</li>
                <li><b>The curve is flat or unrealistic.</b> Check units. Use nm
                for wavelength and films, mm for sensing length, &micro;m for core
                diameter, degrees for angle, and RIU for refractive index.</li>
                <li><b>A dip touches the graph edge.</b> Extend the range and run
                again. Do not trust FWHM or FOM for a clipped resonance.</li>
                <li><b>Sensitivity or FOM is missing.</b> Use at least two analyte
                samples and a positive RIU step. Confirm that the same resonance
                is tracked in both curves.</li>
                <li><b>A custom model fails.</b> Fill every required Sellmeier or
                Drude coefficient. Check decimal separators and the complex-index
                sign convention.</li>
                <li><b>Fiber results look wrong.</b> Check sensing length, core
                diameter, NA, core material, and coating order against the fiber datasheet.</li>
                <li><b>An external file is rejected.</b> Use numeric CSV/TXT data
                with the axis in column 1 and response in column 2. Remove headers
                or unsupported separators if parsing fails.</li>
            </ol>
            <p class="warning"><b>Convergence and mesh:</b> This is a
            transfer-matrix solver, not a spatial mesh solver. There is no mesh
            to refine. Numerical resolution comes from the scan: 0.001° in AIM
            and 0.1 nm in WIM. For parameter sweeps, reduce the parameter step
            and keep the total at 500 points or fewer.</p>
        """,
    },
]


class HelpCenterDialog(QtWidgets.QDialog):
    """Single-window, topic-based Help Center."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HelpCenterDialog")
        self.setWindowTitle("Help Center")
        self.setWindowIcon(QtGui.QIcon("icons/LOGO.png"))
        self.resize(980, 640)
        self.setMinimumSize(840, 520)

        self._topics = HELP_TOPICS
        self._visible_topics = []

        self._build_ui()
        self._apply_style()
        self._populate_topics()

    def _build_ui(self):
        root_layout = QtWidgets.QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        sidebar = QtWidgets.QFrame(self)
        sidebar.setObjectName("HelpSidebar")
        sidebar.setMinimumWidth(280)
        sidebar.setMaximumWidth(320)
        sidebar_layout = QtWidgets.QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(18, 18, 18, 18)
        sidebar_layout.setSpacing(12)

        title = QtWidgets.QLabel("Help Center", sidebar)
        title.setObjectName("HelpTitle")
        sidebar_layout.addWidget(title)

        self.search_input = QtWidgets.QLineEdit(sidebar)
        self.search_input.setPlaceholderText("Search help topics")
        self.search_input.textChanged.connect(self._populate_topics)
        sidebar_layout.addWidget(self.search_input)

        self.topic_list = QtWidgets.QListWidget(sidebar)
        self.topic_list.currentRowChanged.connect(self._render_selected_topic)
        sidebar_layout.addWidget(self.topic_list, stretch=1)

        root_layout.addWidget(sidebar)

        content_frame = QtWidgets.QFrame(self)
        content_frame.setObjectName("HelpContentFrame")
        content_layout = QtWidgets.QVBoxLayout(content_frame)
        content_layout.setContentsMargins(26, 24, 26, 24)
        content_layout.setSpacing(10)

        self.topic_summary = QtWidgets.QLabel(content_frame)
        self.topic_summary.setObjectName("HelpSummary")
        self.topic_summary.setWordWrap(True)
        content_layout.addWidget(self.topic_summary)

        self.topic_browser = QtWidgets.QTextBrowser(content_frame)
        self.topic_browser.setOpenExternalLinks(True)
        self.topic_browser.setObjectName("HelpBrowser")
        content_layout.addWidget(self.topic_browser, stretch=1)

        root_layout.addWidget(content_frame, stretch=1)

    def _apply_style(self):
        self.setStyleSheet(
            """
            QDialog#HelpCenterDialog {
                background-color: #f5f7fb;
            }
            QFrame#HelpSidebar {
                background-color: #17365d;
            }
            QLabel#HelpTitle {
                color: white;
                font: 700 18pt "Segoe UI";
            }
            QLineEdit {
                padding: 8px 10px;
                border: 1px solid #d7dce5;
                border-radius: 4px;
                background: white;
                font: 10pt "Segoe UI";
            }
            QListWidget {
                border: none;
                background: transparent;
                color: #eef4ff;
                font: 10pt "Segoe UI";
                outline: 0;
            }
            QListWidget::item {
                padding: 9px 10px;
                border-radius: 4px;
                margin: 2px 0;
            }
            QListWidget::item:selected {
                background-color: #ffffff;
                color: #17365d;
            }
            QListWidget::item:hover {
                background-color: rgba(255, 255, 255, 45);
            }
            QFrame#HelpContentFrame {
                background-color: #f5f7fb;
            }
            QLabel#HelpSummary {
                color: #41516a;
                font: 11pt "Segoe UI";
                padding-bottom: 8px;
            }
            QTextBrowser#HelpBrowser {
                border: 1px solid #d7dce5;
                border-radius: 6px;
                background: white;
                padding: 18px;
                color: #243044;
                font: 10.5pt "Segoe UI";
            }
            """
        )

    def _populate_topics(self):
        query = self.search_input.text().strip().lower()
        self.topic_list.clear()
        self._visible_topics = []

        for topic in self._topics:
            searchable_text = " ".join(
                [
                    topic["title"],
                    topic["summary"],
                    topic["keywords"],
                    topic["body"],
                ]
            ).lower()
            if query and query not in searchable_text:
                continue

            self._visible_topics.append(topic)
            self.topic_list.addItem(topic["title"])

        if self._visible_topics:
            self.topic_list.setCurrentRow(0)
            return

        self.topic_summary.setText("No help topic matches your search.")
        self.topic_browser.setHtml(
            "<h2>No results</h2><p>Try a broader term such as "
            "<b>layers</b>, <b>analyte</b>, <b>fiber</b>, or <b>results</b>.</p>"
        )

    def _render_selected_topic(self, row):
        if row < 0 or row >= len(self._visible_topics):
            return

        topic = self._visible_topics[row]
        self.topic_summary.setText(topic["summary"])
        self.topic_browser.setHtml(
            f"""
            <html>
            <head>
                <style>
                    h2 {{
                        color: #17365d;
                        font-size: 22px;
                        margin: 0 0 14px 0;
                    }}
                    p, li {{
                        line-height: 1.45;
                        font-size: 14px;
                    }}
                    ol, ul {{
                        margin-top: 6px;
                    }}
                    h3 {{
                        color: #17365d;
                        font-size: 17px;
                        margin: 18px 0 8px 0;
                    }}
                    table {{
                        border-collapse: collapse;
                        width: 100%;
                        margin: 8px 0 14px 0;
                    }}
                    th, td {{
                        border: 1px solid #d7dce5;
                        padding: 6px;
                        vertical-align: top;
                        font-size: 13px;
                    }}
                    th {{
                        background-color: #eaf0f8;
                        color: #17365d;
                    }}
                    .warning {{
                        background-color: #fff4df;
                        border-left: 4px solid #d68a00;
                        padding: 9px 11px;
                    }}
                    a {{
                        color: #145da0;
                    }}
                    b {{
                        color: #17365d;
                    }}
                </style>
            </head>
            <body>{topic["body"]}</body>
            </html>
            """
        )
