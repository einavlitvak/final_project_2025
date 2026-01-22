import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

class PlateLayout:
    """
    Manages the experimental design of a 96-well ELISA plate.
    Uses Pandas DataFrames.
    Includes IO (CSV) and Visualization (PNG).
    """

    def __init__(self, standard_concentrations=[0, 0.1, 0.2, 0.4, 0.8, 1.6, 3.2, 6.4]):
        self.rows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
        self.cols = list(range(1, 13))
        
        self.layout_grid = pd.DataFrame(index=self.rows, columns=self.cols)
        self.type_grid = pd.DataFrame(index=self.rows, columns=self.cols)
        
        self.standard_concentrations = standard_concentrations
        if standard_concentrations:
             self._initialize_standards()

    def _initialize_standards(self):
        if len(self.standard_concentrations) != 8:
            return

        # Portrait Mode: User wants High Concentration at 'A' (Visual Left), Low at 'H' (Visual Right).
        # "Descending from A to H".
        # self.rows = ['A', 'B'...'H']. Index 0=A.
        # standard_concentrations = [0, 0.1...6.4] (Low to High).
        # We want A=6.4.
        # So we MUST reverse the concentrations list.
        
        reversed_concs = list(reversed(self.standard_concentrations))
        
        for i, row in enumerate(self.rows):
            conc = reversed_concs[i] 
            # Column 1 Only (1 Replicate per Plate)
            self.layout_grid.at[row, 1] = f"STD_{conc}"
            self.type_grid.at[row, 1] = "Standard"
            # Column 2 is now empty for samples (Start Col = 2)

    def assign_samples(self, grouped_samples_with_reps, start_col=2):
        """
        Portrait Fill Strategy:
        - Fills 'Visual Columns' (Physical Rows A->H).
        - "Left to Right": A -> B -> C...
        - Inside each visual col, fills Down (Physical Cols start->12).
        - 'Smart Tetris': If sample doesn't fit, find one that does.
        """
        
        # 1. Generate Linear Slots Order: 
        # Physical Row A (Col start..12) -> Row B -> ... -> Row H.
        valid_slots = []
        # Normal Rows (A..H)
        for row_lbl in self.rows:
            c_start = start_col
            for c in range(c_start, 13):
                valid_slots.append( (row_lbl, c) )
        
        total_slots = len(valid_slots)
        
        # 2. Convert Groups to Queue
        queue = list(grouped_samples_with_reps) # Copy
        
        final_assignments = []
        leftovers = []
        
        slot_idx = 0
        
        while slot_idx < total_slots:
            if not queue:
                break
                
            curr_r, curr_c = valid_slots[slot_idx]
            
            # Find how many contiguous slots remain in this Row R starting from C?
            slots_in_row = 0
            for k in range(slot_idx, total_slots):
                if valid_slots[k][0] == curr_r:
                    slots_in_row += 1
                else:
                    break
            
            best_candidate_idx = -1
            
            # Prefer first fit (FIFO)
            for i, (sub, reps) in enumerate(queue):
                if reps <= slots_in_row:
                    best_candidate_idx = i
                    break
            
            if best_candidate_idx == -1:
                # Nothing fits
                slot_idx += slots_in_row # Jump to next row start
                continue
                
            # Place candidate
            sub_samples, sub_reps = queue.pop(best_candidate_idx)
            max_tps = slots_in_row // sub_reps
            tps_to_place = min(len(sub_samples), max_tps)
            
            for i in range(tps_to_place):
                s_id = sub_samples[i]
                for k in range(sub_reps):
                    final_assignments.append( (s_id, valid_slots[slot_idx+k][0], valid_slots[slot_idx+k][1]) )
                slot_idx += sub_reps
            
            if tps_to_place < len(sub_samples):
                remaining = sub_samples[tps_to_place:]
                queue.insert(0, (remaining, sub_reps))
                
        leftovers = queue
        self._render_assignments_linear(final_assignments)
        return leftovers

    def _render_assignments_linear(self, assignments):
         for s_id, r, c in assignments:
             self.layout_grid.at[r, c] = s_id
             self.type_grid.at[r, c] = "Sample"

    def _finalize_leftovers(self, current_leftovers, all_groups, failed_s_id):
        # NOTE: This method is no longer used by the new simplified assign_samples, 
        # but kept for compatibility if needed.
        final_leftovers = []
        found = False
        for sub, reps in all_groups:
            if found:
                final_leftovers.append((sub, reps))
                continue
            if failed_s_id in sub:
                idx = sub.index(failed_s_id)
                final_leftovers.append( (sub[idx:], reps) )
                found = True
        return final_leftovers

        return final_leftovers

    def set_well(self, row_str, col_int, value, type_str):
        if row_str in self.rows and col_int in self.cols:
            self.layout_grid.at[row_str, col_int] = value
            self.type_grid.at[row_str, col_int] = type_str
            return True
        return False
        
    def clear_well(self, row_str, col_int):
        return self.set_well(row_str, col_int, np.nan, np.nan)

    def to_csv(self, filename="plate_layout.csv"):
        # We save the IDs. The Types can be inferred or saved in a separate file.
        # Let's save a simple mapping table: Row, Col, Type, ID
        data = []
        for r in self.rows:
            for c in self.cols:
                val = self.layout_grid.at[r, c]
                t = self.type_grid.at[r, c]
                if pd.notna(val):
                    data.append({'Row': r, 'Col': c, 'Type': t, 'ID': val})
        
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        print(f"Layout saved to {filename}")

    @classmethod
    def from_csv(cls, filename="plate_layout.csv"):
        if not os.path.exists(filename):
            raise FileNotFoundError(f"{filename} not found.")
            
        df = pd.read_csv(filename)
        # Create empty layout (no auto standards, populating from file)
        layout = cls(standard_concentrations=[]) 
        
        for _, row_data in df.iterrows():
            r = row_data['Row']
            c = row_data['Col']
            t = row_data['Type']
            i = row_data['ID']
            layout.set_well(r, c, i, t)
            
        return layout

    def visualize_png(self, filename="plate_layout.png"):
        # Portrait Visualization
        # Rows (A-H) on X-Axis. Cols (1-12) on Y-Axis.
        
        fig, ax = plt.subplots(figsize=(10, 14))
        
        ax.set_xlim(0, 9)
        ax.set_ylim(0, 13)
        
        ax.set_xticks(np.arange(0.5, 8.5, 1))
        # Labels A..H (A=Left).
        ax.set_xticklabels(self.rows) 
        
        ax.set_yticks(np.arange(0.5, 12.5, 1))
        ax.set_yticklabels(list(range(1, 13)))
        ax.invert_yaxis() # 1 at Top.
        
        ax.xaxis.tick_top() 
        ax.grid(True)
        
        # Fill Text
        for r_idx, r in enumerate(self.rows): # 0=A
            for c in self.cols: # 1..12
                val = self.layout_grid.at[r, c]
                if pd.notna(val):
                    text_val = str(val)
                    if len(text_val) > 10: text_val = text_val[:8] + ".."
                    
                    type_val = self.type_grid.at[r, c]
                    color = 'black'
                    bg_color = 'white'
                    if type_val == 'Standard': bg_color = 'lightyellow'
                    elif type_val == 'Sample': bg_color = 'lightblue'
                    
                    # Plot coords:
                    # r_idx 0 (A) -> x=0.5 (Left side). matches ticks.
                    x_pos = r_idx + 0.5
                    y_pos = c - 0.5
                    
                    ax.text(x_pos, y_pos, text_val, 
                            ha='center', va='center', fontsize=8,
                            bbox=dict(facecolor=bg_color, alpha=0.5, edgecolor='none'))
                            
        plt.title("Plate Layout Map (Portrait)")
        plt.tight_layout()
        plt.savefig(filename, dpi=150)
        plt.close()
        print(f"Layout image saved to {filename}")

    def get_layout(self):
        columns_to_return = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        # Ensure integer columns
        self.layout_grid.columns = self.layout_grid.columns.astype(int)
        return self.layout_grid

    def get_types(self):
        self.type_grid.columns = self.type_grid.columns.astype(int)
        return self.type_grid
