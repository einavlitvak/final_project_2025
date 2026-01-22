import sys
import os
import pandas as pd
from src.layout import PlateLayout
from src.data_loader import DataReader
from src.analysis import ElisaAnalyzer
from src.reporting import ElisaReporter

def interactive_edit_post_experiment(layout):
    print("\n--- Post-Experiment Updates ---")
    print("Did any wells fail? (e.g. Spilled, Pipetting Error)")
    print("Commands: 'exclude <Row><Col>' (e.g. exclude A3), 'done'")
    
    while True:
        cmd = input("Update > ").strip()
        if cmd == 'done': break
        
        parts = cmd.split(' ', 1)
        action = parts[0].lower()
        
        if action == 'exclude' and len(parts) >= 2:
            coord = parts[1]
            try:
                r = coord[0].upper()
                c = int(coord[1:])
                # We mark it as Empty so it is ignored in analysis
                # But we might want to keep the ID but flag it? 
                # For now, let's remove it from the layout so it's not grouped.
                layout.clear_well(r, c)
                print(f"Excluded {coord} from analysis.")
            except:
                print("Invalid coordinate.")
        else:
             print("Unknown. Type 'exclude A3' or 'done'.")

def main():
    print("--- ELISA Data Analysis (Post-Experiment) ---")
    
    # 1. Inputs
    input_file = "insulin ELISA ELC1-10 c21 control day 2 + EL196-199 Sweetener 23.5.25.xlsx"
    if not os.path.exists(input_file):
        input_file = input("Enter path to Excel file: ").strip('"')
        
    layout_file = "plate_layout_p1.csv"
    if not os.path.exists(layout_file):
        # Fallback to old default
        if os.path.exists("plate_layout.csv"):
             layout_file = "plate_layout.csv"
        else:
             layout_file = input("Enter path to Layout CSV (e.g. plate_layout_p1.csv): ").strip('"')
    
    # 2. Load Layout
    print(f"Loading Layout from {layout_file}...")
    try:
        layout_mgr = PlateLayout.from_csv(layout_file)
    except Exception as e:
        print(f"Error loading layout: {e}")
        return

    # 3. Post-Experiment Fixes?
    choice = input("Do you need to flag any wells as bad (Spills/Errors)? (y/n): ").lower()
    if choice == 'y':
        interactive_edit_post_experiment(layout_mgr)

    # 4. Load Data
    print(f"Reading Data from: {input_file}")
    reader = DataReader(input_file)
    try:
        data_df = reader.extract_data_grid()
        print("Data Grid Extracted Successfully.")
    except Exception as e:
        print(f"Error reading data: {e}")
        return

    # 5. Analyze
    print("Analyzing Data (Linear Fit)...")
    analyzer = ElisaAnalyzer(layout_mgr, data_df)
    results_df = analyzer.analyze(model_type='linear') 
    
    print("\n--- Results Preview ---")
    print(results_df.head(10).to_string())

    # 6. Report
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
