# ELISA Plate Designer - Project Instructions

## 1. Project Overview
This tool automates the design of ELISA plate layouts. It maximizes plate density, manages multiple experiments, and produces visual maps ("Portrait Mode") and CSV files for analysis.

---

## 2. Design Requirements & Logic

### A. Portrait Orientation (12x8 Grid)
The plate is conceptualized and visualized as a vertical grid:
*   **Dimensions**: 12 Rows (Height) x 8 Columns (Width).
*   **Y-Axis**: Numbers **1** (Top) to **12** (Bottom).
*   **X-Axis**: Letters **A** (Left) to **H** (Right).

### B. Filling Strategy
*   **Direction**:
    1.  **Left-to-Right**: Starts at Visual Row **A** and moves towards **H**.
    2.  **Top-to-Bottom**: Inside each row/column strip, fills indices **1 $\rightarrow$ 12**.
*   **Replicate Placement**: Replicates are always placed **vertically** (e.g., A1, A2, A3 in cells A1, A2, A3).
*   **Smart "Tetris" Optimization**:
    *   The system ensures **100% density**.
    *   If a sample (e.g., 3 replicates) cannot fit in the remaining slots of a column, the system **looks ahead** in the queue.
    *   It pulls a smaller sample (e.g., 2 replicates) to fill the gap before moving to the next column.

### C. Calibration Curve (Standards)
*   **Location**: Standards occupy **Column 1 only** on **EVERY** plate.
*   **Consistency**: Plate 1, Plate 2, etc. all follow this rule (1 Column of Standards).
*   **Concentration Order (Descending)**:
    *   **Row A (Top/Left)**: Highest Concentration (`6.4`).
    *   **Row H (Bottom/Right)**: Lowest Concentration (`0`).

### D. Multi-Experiment & Overflow
*   **Input**: You can define multiple distinct experiments (e.g., Exp A, Exp B) in a single run.
*   **Overflow**: Samples automatically spill over to **Plate 2**, **Plate 3**, etc., if they exceed capacity.
*   **Plate 2+ Logic**: Follows the exact same layout rules (Standards in Col 1, Fill Start at Col 2).

---

## 3. How to Run

### Step 1: Activate Environment
Open your terminal (PowerShell) and run:
```powershell
.\.venv\Scripts\Activate.ps1
```
*(You should see `(.venv)` appear at the start of your command prompt)*

### Step 2: Run the Designer
```powershell
python elisa_design.py
```

### Step 3: Provide Inputs
Follow the on-screen prompts:
1.  **Number of Experiments**: (e.g., 2)
2.  **Experiment Details**:
    *   Subject Names (comma separated types, e.g., `S1, S2, S3`)
    *   Number of Timepoints (e.g., 3)
    *   Number of Replicates (e.g., 2)
3.  **Review**: The script generates a preview PNG. Type `n` (no changes) to confirm and save.

---

## 4. Outputs
For each generated plate (p1, p2...), you get:
1.  **PNG Image** (`plate_layout_p1.png`):
    *   Visual map with easy-to-read labels.
    *   Color-coded (Yellow=Standard, Blue=Sample).
2.  **CSV File** (`plate_layout_p1.csv`):
    *   Data file containing `Row`, `Col`, `ID`, and `Type` for analysis.
