import sys
import pandas as pd
from src.layout import PlateLayout

class DebugLayout(PlateLayout):
    pass 

def run_debug():
    # User's exact scenario
    # Exp A: 9 subjects (3 TPs, 2 Reps)
    exp1_samples = []
    for i in range(1, 10):
        s_id = f"A{i}"
        exp1_samples.append( ([f"{s_id}_t2", f"{s_id}_t1", f"{s_id}_t0"], 2) )
        
    # Exp B: 6 subjects (2 TPs, 3 Reps)
    exp2_samples = []
    for i in range(1, 7):
        s_id = f"B{i}"
        exp2_samples.append( ([f"{s_id}_t1", f"{s_id}_t0"], 3) )
        
    # Exp C: 6 subjects (2 TPs, 2 Reps)
    exp3_samples = []
    for i in range(1, 7):
        s_id = f"C{i}"
        exp3_samples.append( ([f"{s_id}_t1", f"{s_id}_t0"], 2) )
        
    all_groups = exp1_samples + exp2_samples + exp3_samples
    
    print(f"Total Groups: {len(all_groups)}")
    
    layout = DebugLayout()
    print("--- Assigning Portrait Layout (StartCol=2) ---")
    leftovers = layout.assign_samples(all_groups, start_col=2)
    
    df = layout.get_layout()
    
    # 1. Verify Standards Order
    # Row H (index 7) should be STD_0 (Low)
    # Row A (index 0) should be STD_6.4 (High)
    h_std = df.at['H', 1]
    a_std = df.at['A', 1]
    print(f"\nStandards Check:")
    print(f"Row H (Visual Right): {h_std} (Expected Low)")
    print(f"Row A (Visual Left): {a_std} (Expected High)")
    
    # 2. Verify Fill Order (Left to Right = A -> B)
    # Row A should be filled with A1..A2...
    print("\nVisual Row A (Physical Row A) Content:")
    print(df.loc['A'].dropna().values)
    
    # 3. Verify Smart Queue (Exp C filling gap in Row B?)
    print("\nVisual Row B (Physical Row B) Content:")
    print(df.loc['B'].dropna().values)
    
    c_found = False
    for r in layout.rows:
        for c in layout.cols:
            val = df.at[r, c]
            if isinstance(val, str) and "C" in val:
                c_found = True
                break
    print(f"Exp C Found in Grid? {c_found}")

    print(f"\nLeftovers: {len(leftovers)}")
    if leftovers:
        print(f"First Leftover: {leftovers[0][0][0]}")

if __name__ == "__main__":
    run_debug()
