import unittest
import pandas as pd
import numpy as np
import sys
import os

# Add parent directory to path to import elisa_core
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'analyzer'))

import elisa_core

class TestElisaCore(unittest.TestCase):
    
    def test_fit_calibration_model_perfect_line(self):
        """Test linear regression with perfect data y=2x+1."""
        data = pd.DataFrame({
            'Type': ['Calibration', 'Calibration', 'Calibration'],
            'Concentration': [0, 10, 20],
            'OD_Corr': [1, 21, 41] # y = 2x + 1
        })
        
        model, means = elisa_core.fit_calibration_model(data)
        
        self.assertAlmostEqual(model['slope'], 2.0)
        self.assertAlmostEqual(model['intercept'], 1.0)
        self.assertAlmostEqual(model['r_squared'], 1.0)
        
    def test_calculate_concentrations(self):
        """Test concentration calculation from model."""
        model = {'slope': 2.0, 'intercept': 1.0, 'r_squared': 1.0}
        
        data = pd.DataFrame({
            'Type': ['Experiment', 'Experiment'],
            'OD_Corr': [5.0, 21.0], # Expected: (5-1)/2 = 2, (21-1)/2 = 10
            'Concentration': [np.nan, np.nan]
        })
        
        res = elisa_core.calculate_concentrations(data, model)
        
        self.assertAlmostEqual(res.loc[0, 'Calculated_Conc'], 2.0)
        self.assertAlmostEqual(res.loc[1, 'Calculated_Conc'], 10.0)
        
    def test_extract_grid_structure(self):
        """Test grid extraction from a mocked dataframe."""
        # Create a dataframe mimicking Excel grid
        # Row 0: Header '<>'
        # Row 1: 'A' ... 8 values
        rows = []
        rows.append(['<>'] + [np.nan]*12) # 0
        rows.append(['A'] + [0.1]*12)     # 1
        rows.append(['B'] + [0.2]*12)     # 2
        # ... fill rest to avoid index error
        for i in range(10): rows.append([np.nan]*13)
        
        df = pd.DataFrame(rows)
        
        grid = elisa_core.extract_grid(df, 1)
        
        self.assertEqual(len(grid), 96) # 8 rows * 12 columns
        # Check first row (A)
        self.assertEqual(grid.iloc[0]['Well'], 'A1')
        self.assertAlmostEqual(grid.iloc[0]['OD'], 0.1)
        # Check empty row (C is index 24)
        self.assertTrue(pd.isna(grid.iloc[24]['OD']))
        
    def test_merge_and_correct(self):
        """Test merging of 450 and 630 dataframes."""
        layout = pd.DataFrame({'Well': ['A1'], 'Type': ['Sample']})
        od450 = pd.DataFrame({'Well': ['A1'], 'OD': [1.0]})
        od630 = pd.DataFrame({'Well': ['A1'], 'OD': [0.1]})
        
        merged = elisa_core.merge_and_correct(layout, od450, od630)
        
        self.assertAlmostEqual(merged.iloc[0]['OD_Corr'], 0.9)

    def test_run_statistical_analysis_duplicate_names(self):
        """Test stats when two different subjects have the same name."""
        # Create dataframe with 3 subjects having name "Control"
        # We need n >= 3 for the stats logic to proceed
        data = pd.DataFrame({
            'Type': ['Experiment'] * 6,
            'Subject': [1, 1, 2, 2, 3, 3],
            'Subject Name': ['Control', 'Control', 'Control', 'Control', 'Control', 'Control'],
            'Timepoint': ['t0', 't1', 't0', 't1', 't0', 't1'],
            'Calculated_Conc': [10, 20, 12, 22, 11, 21]
        })
        
        config = {
            'timepoints': ['t0', 't1'],
            'paired': True,
            'tails': 'two-sided',
            'posthoc': False
        }
        
        # This should NOT start a ValueError
        try:
            results = elisa_core.run_statistical_analysis(data, config)
            self.assertIn('p_value', results)
        except ValueError as e:
            self.fail(f"run_statistical_analysis raised ValueError with duplicate names: {e}")

if __name__ == '__main__':
    unittest.main()
