# ELISA Plate Specifications (Manual Layout Context)

## 1. Grid Geometry
- **Format**: Standard 96-well plate
- **Dimensions**: 8 Columns × 12 Rows
- **Columns**: Labelled **A** through **H**
- **Rows**: Labelled **1** through **12**
- **Total Wells**: 96

## 2. Fixed Zones (Calibration Curve)
- **Location**: Rows 1 and 2 (Indices 0 and 1)
- **Layout**: Horizontal across all 8 columns
- **Purpose**: Standard Calibration Curve
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
The layout allows defining blocks at these nested levels:

### Level 1: Experiment
- **Definition**: A high-level container for a batch of work.
- **Attributes**: `Experiment ID` (integer or string).

### Level 2: Subject
- **Definition**: A biological source (e.g., Mouse #1, Patient A).
- **Attributes**: `Subject ID`.
- **Relationship**: Belongs to exactly one Experiment.

### Level 3: Sample (Condition/Timepoint)
- **Definition**: A unique condition for a subject (e.g., t=0, t=1hr).
- **Attributes**: `Sample ID` (numbered 1..N).
- **Relationship**: Belongs to exactly one Subject.

### Level 4: Replicate
- **Definition**: Technical repeats of the same sample.
- **Attributes**: `Replicate ID` (R1, R2, R3...).
- **Relationship**: Belongs to exactly one Sample.
- **Visual**: Replicates are effectively the individual wells.

## 4. Output Requirements
- **Visual**: Grid view showing sample labels.
- **Data**: CSV export of the defined layout.
