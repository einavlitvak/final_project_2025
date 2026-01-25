# ELISA Data Analyzer

**Project for WIS Python Course**

## Project Proposal / Description

### 1. What does this project do?
This project automates the analysis of ELISA (Enzyme-Linked Immunosorbent Assay) experiments. Manual analysis of ELISA data from Tecan plate readers is time-consuming and prone to precision errors. This project provides a **suite of two tools**:

1.  **ELISA Layout Designer**: A visual tool to map your plate (Standards, Samples, Blanks) and export a standard CSV map.
2.  **ELISA Data Analyzer**: A computational tool that takes the layout and raw instrument data to:
    -   **Parse** raw Tecan Excel/CSV output files automatically.
    -   **Correct** optical density (OD) readings (OD450 - OD630) and subtract blanks.
    -   **Calibrate** concentrations using a linear regression model from standard curves.
    -   **Analyze** statistics automatically (Normality, Homogeneity, T-Test/ANOVA, Post-Hoc).
    -   **Visualize** results with publication-ready plots.
    -   **Export** a "Master File" combining raw data and full validation reports.

### 2. Input and Output
*   **Input**:
    *   **Layout File**: A CSV defining which well contains which sample/standard (created via the built-in Layout Designer).
    *   **Instrument File**: The raw `.xlsx` or `.csv` export from the Tecan Infinite M200 Pro machine.
*   **Output**:
    *   **Master Excel File**: Appends a new sheet with Raw Data + Analysis Tables.
    *   **Plots**: `calibration_curve.png`, `results_bar_graph.png`, `significance_plot.png`.

### 3. Technicalities
#### Dependencies
*   `pandas`, `numpy`: Data manipulation.
*   `scipy`: Advanced statistical testing (stats).
*   `matplotlib`, `seaborn`: Plotting.
*   `openpyxl`: Excel I/O.
*   `tkinter`: GUI (standard library).

#### Installation
1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

#### Running the Project
1.  **Define Layout** (if needed):
    ```bash
    python designer/elisa_layout_designer.py
    ```
2.  **Run Analysis**:
    ```bash
    python analyzer/elisa_data_analyzer.py
    ```
3.  Follow the GUI prompts to select files and configure analysis parameters.

    > **Quick Start with Examples**:
    > *   For **Layout CSV**, select: `example_layout.csv`
    > *   For **Instrument Excel**, select: `insulin ELISA example.xlsx`
    > *   For **Master Excel**, select: `insulin ELISA example_master.xlsx`
    

#### Testing
To verify the core logic of both tools:
```bash
python -m unittest discover tests
```

---
*This project was written as part of the [WIS Python programming course](https://github.com/Code-Maven/wis-python-course-2025-10).*
