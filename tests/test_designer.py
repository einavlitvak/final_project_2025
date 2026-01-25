import unittest
import pandas as pd
import sys
import os

# Add parent directory to path to import designer_core
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'designer'))

import designer_core

class TestDesignerCore(unittest.TestCase):
    
    def test_fill_cells_vertical(self):
        """Test vertical fill logic (Unique samples vary by Column)."""
        # Select 2x2 grid: (0,0) to (1,1)
        # Vertical: (0,0) is s0_r1, (0,1) is s0_r2. (1,0) is s1_r1, (1,1) is s1_r2.
        
        updates, next_id = designer_core.fill_cells(0, 0, 1, 1, 1, 1, 0, 'vertical')
        
        self.assertEqual(len(updates), 4)
        
        # Col 0, Row 0 -> Sample 0
        self.assertEqual(updates[(0,0)]['samp'], 0)
        self.assertEqual(updates[(0,0)]['rep'], 1)
        
        # Col 0, Row 1 -> Sample 0 (Rep 2)
        self.assertEqual(updates[(0,1)]['samp'], 0)
        self.assertEqual(updates[(0,1)]['rep'], 2)
        
        # Col 1, Row 0 -> Sample 1
        self.assertEqual(updates[(1,0)]['samp'], 1)
        self.assertEqual(updates[(1,0)]['rep'], 1)
        
        self.assertEqual(next_id, 2)
        
    def test_fill_cells_horizontal(self):
        """Test horizontal fill logic (Unique samples vary by Row)."""
        # Select 2x2 grid: (0,0) to (1,1)
        # Horizontal: (0,0) is s0_r1, (1,0) is s0_r2. (0,1) is s1_r1...
        
        updates, next_id = designer_core.fill_cells(0, 0, 1, 1, 1, 1, 0, 'horizontal')
        
        # Row 0, Col 0 -> Sample 0
        self.assertEqual(updates[(0,0)]['samp'], 0)
        # Row 0, Col 1 -> Sample 0 (Rep 2)
        self.assertEqual(updates[(1,0)]['samp'], 0)
        
        # Row 1, Col 0 -> Sample 1
        self.assertEqual(updates[(0,1)]['samp'], 1)
        
        self.assertEqual(next_id, 2)

    def test_grid_to_dataframe_and_back(self):
        """Test round trip conversion."""
        # Setup mock grid
        grid = {
            (0,0): {'type': 'CAL', 'conc': 100.0},
            (1,0): {'type': 'EXP', 'exp': 1, 'subj': 1, 'samp': 99, 'rep': 1}
        }
        names = {(1, 1): "TestSubject"}
        
        # Export
        df = designer_core.grid_to_dataframe(grid, names)
        
        # Verify DF content
        row_cal = df[df['Type'] == 'Calibration'].iloc[0]
        self.assertEqual(float(row_cal['Concentration']), 100.0)
        
        row_exp = df[df['Type'] == 'Experiment'].iloc[0]
        self.assertEqual(row_exp['Subject Name'], "TestSubject")
        
        # Import
        new_grid, new_names, state = designer_core.dataframe_to_grid(df)
        
        # Verify Grid content
        self.assertEqual(new_grid[(0,0)]['type'], 'CAL')
        self.assertEqual(new_grid[(1,0)]['samp'], 99)
        self.assertEqual(new_names[(1,1)], "TestSubject")

if __name__ == '__main__':
    unittest.main()
