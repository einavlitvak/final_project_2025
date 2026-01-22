import sys
import os
import pandas as pd
from src.layout import PlateLayout
from src.data_loader import DataReader
from src.analysis import ElisaAnalyzer
from src.reporting import ElisaReporter

def get_user_config():
    print("\n--- Experiment Configuration ---")
    
    # 1. Subjects
    subjects_input = input("Enter Subject Names (comma separated): ")
    subjects = [s.strip() for s in subjects_input.split(',') if s.strip()]
    
    if not subjects:
        print("No subjects entered. Using dummy 'Sample'.")
        subjects = ['Sample']

    # 2. Timepoints
    try:
        n_points = int(input("Enter number of timepoints (e.g., 1, 2, 3): "))
    except ValueError:
        print("Invalid number. Defaulting to 1.")
        n_points = 1
        
    sample_ids = []
    for subj in subjects:
        for t in range(n_points):
            s_id = f"{subj}_t{t}" if n_points > 1 else subj
            sample_ids.append(s_id)
            
    print(f"Generated {len(sample_ids)} unique samples/conditions.")

    # 3. Replicates
    try:
        reps = int(input("Enter number of replicates (2 or 3): "))
    except ValueError:
        reps = 2

    return sample_ids, reps

def main():
    print("--- ELISA Data Analysis Tool (Advanced Mode) ---")
    
    input_file = "insulin ELISA ELC1-10 c21 control day 2 + EL196-199 Sweetener 23.5.25.xlsx"
    if not os.path.exists(input_file):
        input_file = input("Enter path to Excel file: ").strip('"')
        if not os.path.exists(input_file):
            print("File not found.")
            return

    standards = [0, 0.1, 0.2, 0.4, 0.8, 1.6, 3.2, 6.4]
    
    sample_ids, replicates = get_user_config()
    
    # 1. Setup Layout
    print("Setting up Vertical Strip Layout...")
    layout_mgr = PlateLayout(standard_concentrations=standards)
    layout_mgr.assign_samples(sample_ids, replicates=replicates)

    # 2. Load Data
    print(f"Reading Data from: {input_file}")
    reader = DataReader(input_file)
    try:
        data_df = reader.extract_data_grid()
        print("Data Grid Extracted Successfully.")
    except Exception as e:
        print(f"Error reading data: {e}")
        return

    # 3. Analyze
    print("Analyzing Data (Linear Fit)...")
    analyzer = ElisaAnalyzer(layout_mgr, data_df)
    results_df = analyzer.analyze(model_type='linear') 
    
    print("\n--- Results Preview ---")
    print(results_df.head(10).to_string())

    # 4. Report
    print("Generating Report...")
    reporter = ElisaReporter(input_file)
    try:
        img_path = "calibration_curve_linear.png"
        if analyzer.fitter:
             reporter.plot_calibration_curve(analyzer.fitter, img_path)
             
        reporter.save_results(results_df, image_path=img_path)
        print("Analysis Complete. Results and Plot appended to Excel.")
    except Exception as e:
        print(f"Error writing to excel: {e}")

if __name__ == "__main__":
    main()
