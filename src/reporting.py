import pandas as pd
import matplotlib.pyplot as plt
import openpyxl
from openpyxl.drawing.image import Image as ExcelImage
import numpy as np
import os

class ElisaReporter:
    def __init__(self, original_file):
        self.file_path = original_file

    def plot_calibration_curve(self, fitter, output_path='calibration_curve.png'):
        """
        Generates a plot of the standard curve.
        """
        if fitter is None or fitter.params is None:
            print("No fitter to plot.")
            return None

        plt.figure(figsize=(8, 6))
        
        # Plot Data Points
        plt.scatter(fitter.conc, fitter.abs, color='blue', label='Standards')
        
        # Plot Line
        x_range = np.linspace(0, max(fitter.conc)*1.1, 100)
        
        y_pred = None
        if fitter.model_type == 'linear':
            slope, intercept = fitter.params
            y_pred = slope * x_range + intercept
        elif fitter.model_type == 'linear_log':
             # Plotting log-log is tricky on linear scale. 
             # Let's just plot the points.
             pass
        elif fitter.model_type == '4pl':
            def fourPL(x, A, B, C, D):
                return D + (A - D) / (1.0 + (x / C)**B)
            y_pred = fourPL(x_range, *fitter.params)
            
        if y_pred is not None:
            plt.plot(x_range, y_pred, 'r--', label=f'Fit ({fitter.model_type})')
        
        plt.title(f"Standard Curve ($R^2 = {fitter.r_squared:.4f}$)")
        plt.xlabel("Concentration (ng/ml)")
        plt.ylabel("Absorbance")
        plt.legend()
        plt.grid(True, linestyle=':')
        
        plt.savefig(output_path, dpi=100)
        plt.close()
        return output_path

    def save_results(self, results_df, image_path=None):
        """
        Appends a new sheet 'Analysis Results'
        """
        # We use openpyxl directly to avoid pandas writer append issues
        # But pandas to_excel is convenient.
        
        with pd.ExcelWriter(self.file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            results_df.to_excel(writer, sheet_name='Analysis Results', index=False)
            
        if image_path:
            self._add_image_to_excel(image_path)
            
    def _add_image_to_excel(self, img_path):
        if not os.path.exists(img_path): return
        
        wb = openpyxl.load_workbook(self.file_path)
        if 'Analysis Results' in wb.sheetnames:
            ws = wb['Analysis Results']
            img = ExcelImage(img_path)
            # Add to right of table (approx Column G)
            ws.add_image(img, 'G2') 
            wb.save(self.file_path)
