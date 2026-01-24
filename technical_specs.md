# ELISA Plate Designer - Technical Specifications

## 1. Architecture
- **Framework**: `tkinter` (Python Standard Library) for GUI.
- **Data Handling**: `pandas` for CSV Import/Export.
- **Image Generation**: `Pillow` (PIL) for PNG Export.
- **Entry Point**: `elisa_layout_designer.py`.

## 2. Class: `ElisaPlateDesigner`

### State Management
-   `grid_data`: Dictionary mapping `(col, row)` tuples to cell data dicts.
    -   Key: `(0..7, 0..11)`
    -   Value: `{'type', 'exp', 'subj', 'samp', 'rep', 'conc', 'id_str'}`
-   `history`: List of deep copies of `grid_data` (+ state vars) for Undo functionality.
-   `subject_names`: Dictionary `(exp, subj) -> tk.StringVar` for binding sidebar inputs to grid labels.

### Key Key Logic Flows

#### Selection & Filling (`apply_selection`)
1.  **Input**: Selection rectangle (start_col, start_row, end_col, end_row).
2.  **Validation**: Prevents overwriting Rows 0-1 (Calibration).
3.  **Iteration**:
    -   **Vertical Mode**: Outer loop Cols (Samples), Inner loop Rows (Replicates).
    -   **Horizontal Mode**: Outer loop Rows (Samples), Inner loop Cols (Replicates).
4.  **Data Creation**: Assigns ExpID, SubjID, SampID (t0, t1...), RepID to `grid_data`.

#### Drawing Borders (`draw_overlays`)
-   Iterates through all cells.
-   Checks 4 neighbors (Up, Down, Left, Right).
-   Draws a thick black line if the neighbor is "different".
-   **Definition of Different**:
    -   Neighbor is None/Empty.
    -   Neighbor is Calibration.
    -   Neighbor Experiment ID != Current Experiment ID.
    -   Neighbor Subject ID != Current Subject ID.

#### Export (`export_png`)
-   Replicates the `draw_grid` logic using `PIL.ImageDraw`.
-   Uses `arial.ttf` if available, falls back to default bitmap font.
-   Draws text labels centered in cells.

## 3. Data Dictionary (Internal)
| Key | Type | Description |
| :--- | :--- | :--- |
| `type` | str | 'CAL' (Calibration) or 'EXP' (Experiment) |
| `exp` | int | Experiment ID (1-based) |
| `subj` | int | Subject ID (1-based, resets? No, usually handled by logic) |
| `samp` | int | Sample ID (0-based, t0..) |
| `rep` | int | Replicate ID (1-based) |
| `conc` | float | Concentration (Calibration only) |

## 4. Dependencies
-   `pandas`: `>= 1.0`
-   `Pillow`: `>= 8.0`
-   `tkinter`: Built-in
