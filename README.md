# ELISA Plate Layout Designer

A Python GUI application for designing and populating ELISA plate layouts. This tool allows researchers to visually map out experiments on a standard 96-well plate, manage subjects and samples, and export the final layout to PNG or CSV.

## Features

-   **Interactive Grid**: 8x12 grid representing a 96-well plate.
-   **Drag-to-Select**: Easily populate wells by clicking and dragging.
-   **Calibration Curve**: Pre-filled calibration rows (1 and 2).
-   **Experiment & Subject Management**:
    -   Automatically groups samples by Subject and Experiment.
    -   Visual distinction between different experiments (color-coded).
    -   Black borders delineate distinct subjects/experiments.
-   **Replicate Handling**:
    -   Supports both Vertical (default) and Horizontal replicate orientation.
    -   Visual lines connect replicates of the same sample.
-   **Custom Subject Names**: Sidebar interface to name subjects (e.g., "Mouse 1") which updates the grid in real-time.
-   **Sample Counter**: Automatically increments sample IDs (t0, t1, t2...) starting from t0.
-   **Export/Import**:
    -   Export layout to **PNG** image for presentations.
    -   Export data to **CSV** for analysis.
    -   Import **CSV** to restore a previous session.
-   **Undo Support**: Undo the last action with `Ctrl+Z`.

## Installation

1.  **Prerequisites**: Python 3.8 or higher.
2.  **Clone/Download** this repository.
3.  **Create a Virtual Environment** (recommended):
    ```bash
    python -m venv .venv
    # Windows
    .\.venv\Scripts\activate
    # Mac/Linux
    source .venv/bin/activate
    ```
4.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *Note: `tkinter` is included with standard Python installations.*

## Usage

Run the application:
```bash
python elisa_layout_designer.py
```

### Controls

| Action | Key / Input | Description |
| :--- | :--- | :--- |
| **Close Subject** | `Space Bar` | Marks the current Subject as finished. The next selection will start a new Subject. |
| **Close Experiment** | `E` | Marks the current Experiment as finished. The next selection will start a new Experiment (new color). |
| **Rotate Replicates** | `R` | Toggles replicate orientation between Vertical (stack down) and Horizontal (side-by-side). |
| **Undo** | `Ctrl+Z` | Undoes the last grid addition. |
| **Name Subject** | Sidebar Input | Type in the text field in the right sidebar to rename a subject. |

### Workflow Example

1.  Launch the app.
2.  **Add Subject 1**: Drag across `A3` to `A4` (2 replicates).
3.  **Add Subject 2**: Press `Space`, then drag `B3` to `B4`.
4.  **Rename**: Look at the sidebar, find "S1", type "Control".
5.  **New Experiment**: Press `E`. Drag `A5`...
6.  **Export**: Use the **File** menu to save your work.
