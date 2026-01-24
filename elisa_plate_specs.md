# ELISA Plate Specifications (As Built)

## 1. Grid Geometry
- **Format**: Standard 96-well plate
- **Dimensions**: 8 Columns × 12 Rows
- **Columns**: Labelled **A** through **H** (visual) / 0-7 (internal)
- **Rows**: Labelled **1** through **12** (visual) / 0-11 (internal)
- **Total Wells**: 96

## 2. Fixed Zones (Calibration Curve)
- **Location**: Rows 1 and 2 (Indices 0 and 1)
- **Layout**: Horizontal across all 8 columns
- **Visual**: Light Red background
- **Concentrations**:
  - A1/A2: 6.4
  - B1/B2: 3.2
  - C1/C2: 1.6
  - D1/D2: 0.8
  - E1/E2: 0.4
  - F1/F2: 0.2
  - G1/G2: 0.1
  - H1/H2: 0.0 (Blank)

## 3. Data Hierarchy Definitions
### Level 1: Experiment
- **Definition**: A high-level container for a batch of work.
- **Attributes**: `Experiment ID` (integer, starts at 1).
- **Visual**: Each experiment is assigned a distinct pastel color (Green, Blue, Yellow, Pink, Cyan, Orange).
- **Logic**: Creating a new experiment (Key: `E`) resets the Subject ID counter (optional) and changes the active color.

### Level 2: Subject
- **Definition**: A biological source (e.g., Mouse #1, Patient A).
- **Attributes**: 
    - `Subject ID` (integer, resets per experiment).
    - `Subject Name` (string, user-editable via Sidebar).
- **Visual**: 
    - Text Label: "Name" (or S# if empty).
    - Border: Thick black border surrounds contiguous cells of the same Subject.
- **Logic**: Pressing `Space` closes the current subject; next selection increments ID.

### Level 3: Sample (Condition/Timepoint)
- **Definition**: A unique condition for a subject.
- **Attributes**: `Sample ID` (numbered t0, t1, t2...).
- **Prefix**: 't' (e.g., t0).
- **Indexing**: Starts at 0.

### Level 4: Replicate
- **Definition**: Technical repeats of the same sample.
- **Attributes**: `Replicate ID` (1, 2, 3...).
- **Visual**: Blue lines connect replicates of the same sample.
- **Orientation Modes**:
    1.  **Vertical** (Default): Samples usually in columns, Replicates stacked vertically.
    2.  **Horizontal** (Key: `R`): Samples usually in rows, Replicates side-by-side.

## 4. UI & Controls
-   **Sidebar**: Lists subjects grouped by Experiment. Input fields allow real-time renaming.
-   **Shortcuts**:
    -   `Space`: Close Subject.
    -   `E`: Close Experiment.
    -   `R`: Rotate Orientation.
    -   `Ctrl+Z`: Undo.

## 5. Output Requirements
-   **CSV Export**: Columns include Well, Type, Concentration, Experiment, Subject, Subject Name, Sample, Replicate.
-   **PNG Export**: High-resolution generated image matching the grid visualization.
-   **CSV Import**: Restore application state from saved CSV.
