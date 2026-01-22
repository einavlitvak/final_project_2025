import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
import warnings

class CurveFitter:
    """
    Handles calibration curve fitting.
    """
    def __init__(self, standards_conc, standards_abs, model_type='linear'):
        """
        Args:
            model_type (str): 'linear' (Raw), 'linear_log' (Log-Log), or '4pl'.
        """
        self.conc = np.array(standards_conc)
        self.abs = np.array(standards_abs)
        self.model_type = model_type
        self.params = None
        self.r_squared = None

    def fit(self):
        # Filter NaNs
        mask = ~np.isnan(self.abs) & ~np.isnan(self.conc)
        x = self.conc[mask]
        y = self.abs[mask]
        
        if len(x) < 2:
            print("Not enough points for fitting.")
            return

        if self.model_type == 'linear':
            # Linear: Abs = m * Conc + c
            slope, intercept = np.polyfit(x, y, 1)
            self.params = (slope, intercept)
            y_pred = slope * x + intercept
            self.r_squared = self._calculate_r2(y, y_pred)

        elif self.model_type == 'linear_log':
             # Log-Log: Log(Abs) vs Log(Conc)
             # Handle 0/negative
             mask_log = (x > 0) & (y > 0)
             x_log = np.log10(x[mask_log])
             y_log = np.log10(y[mask_log])
             
             if len(x_log) < 2:
                 self.model_type = 'linear'
                 self.fit()
                 return

             slope, intercept = np.polyfit(x_log, y_log, 1)
             self.params = (slope, intercept)
             
             # R2 on transformed data? or original? Usually transformed.
             y_pred_log = slope * x_log + intercept
             self.r_squared = self._calculate_r2(y_log, y_pred_log)

        elif self.model_type == '4pl':
            # 4 Parameter Logistic
            # y = d + (a - d) / (1 + (x / c)^b)
            def fourPL(x, A, B, C, D):
                return D + (A - D) / (1.0 + (x / C)**B)
            
            # Initial guesses
            # A (min), B (slope), C (inflection), D (max)
            p0 = [np.min(y), 1.0, np.mean(x), np.max(y)]
            try:
                popt, _ = curve_fit(fourPL, x, y, p0=p0, maxfev=5000)
                self.params = popt
                y_pred = fourPL(x, *popt)
                self.r_squared = self._calculate_r2(y, y_pred)
            except Exception as e:
                print(f"4PL Fit failed: {e}. Falling back to Linear.")
                self.model_type = 'linear'
                self.fit()

    def predict_concentration(self, absorbance):
        if self.params is None: return 0.0

        try:
            if self.model_type == 'linear':
                slope, intercept = self.params
                conc = (absorbance - intercept) / slope
                return conc if conc > 0 else 0.0

            elif self.model_type == 'linear_log':
                # log(y) = m * log(x) + c
                # log(x) = (log(y) - c) / m
                if absorbance <= 0: return 0.0
                slope, intercept = self.params
                log_abs = np.log10(absorbance)
                log_conc = (log_abs - intercept) / slope
                return 10**log_conc

            elif self.model_type == '4pl':
                A, B, C, D = self.params
                # Inverse 4PL
                if absorbance >= D: return np.inf 
                if absorbance <= A: return 0.0
                
                term1 = (A - D) / (absorbance - D) - 1
                if term1 <= 0: return 0.0
                return C * (term1**(1/B))
        except:
            return np.nan

    def _calculate_r2(self, y_true, y_pred):
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        return 1 - (ss_res / ss_tot)


class ElisaAnalyzer:
    def __init__(self, layout, data_df):
        """
        Args:
            layout (PlateLayout): Layout object.
            data_df (pd.DataFrame): 8x12 Grid of absorbance.
        """
        self.layout = layout
        self.data = data_df
        self.results = []
        self.fitter = None

    def analyze(self, model_type='linear'):
        # 1. Extract Standards using Pandas loc/iloc
        # Layout and Data are DataFrames
        layout_df = self.layout.get_layout()
        type_df = self.layout.get_types()
        
        std_conc = []
        std_abs = []
        
        # Iterate over DataFrame
        for r in layout_df.index:
            for c in layout_df.columns:
                if type_df.at[r, c] == 'Standard':
                     val_str = layout_df.at[r, c]
                     try:
                        conc = float(val_str.split('_')[1])
                        abs_val = self.data.at[r, c] # Ensure data_df has same index/cols
                        if pd.notna(abs_val):
                            std_conc.append(conc)
                            std_abs.append(abs_val)
                     except: pass

        # 2. Fit Curve
        self.fitter = CurveFitter(std_conc, std_abs, model_type=model_type)
        self.fitter.fit()

        # 3. Process Samples
        samples_map = {}
        
        for r in layout_df.index:
            for c in layout_df.columns:
                if type_df.at[r, c] == 'Sample':
                    s_id = layout_df.at[r, c]
                    abs_val = self.data.at[r, c]
                    
                    if s_id not in samples_map: samples_map[s_id] = []
                    if pd.notna(abs_val):
                        samples_map[s_id].append(abs_val)

        # 4. Calculate Results
        final_rows = []
        for sample_id, absorbances in samples_map.items():
            n = len(absorbances)
            mean_abs = np.mean(absorbances) if n > 0 else 0
            std_abs = np.std(absorbances, ddof=1) if n > 1 else 0
            cv = (std_abs / mean_abs * 100) if mean_abs > 0 else 0
            
            concs = [self.fitter.predict_concentration(a) for a in absorbances]
            mean_conc = np.mean(concs) if n > 0 else 0
            
            note = "High CV (>15%)" if cv > 15 else ""

            final_rows.append({
                "Sample ID": sample_id,
                "Mean Abs": round(mean_abs, 3),
                "Conc (ng/ml)": round(mean_conc, 3),
                "CV %": round(cv, 1),
                "QC Note": note
            })

        return pd.DataFrame(final_rows)
