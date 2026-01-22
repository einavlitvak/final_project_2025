import sys
import os
import pandas as pd
from src.layout import PlateLayout

def get_user_config():
    print("\n--- Experiment Configuration ---")
    
    all_grouped_samples = []
    # We enforce same replicates for the whole plate for simplicity in layout logic, 
    # OR we store replicates with the group? 
    # Layout.assign_samples takes one 'replicates' arg. 
    # If experiments have different replicates, we need to pass that info along.
    # Let's verify with user? User said "ask about timepoints and replicates for each experiment".
    # So we need to store (samples_list, replicates) tuples.
    
    try:
        n_experiments = int(input("How many different experiments are on this plate? (e.g. 1): "))
    except ValueError: n_experiments = 1
    
    for i in range(n_experiments):
        print(f"\n-- Experiment {i+1} --")
        subjects_input = input("Enter Subject Names (comma separated): ")
        subjects = [s.strip() for s in subjects_input.split(',') if s.strip()]
        if not subjects: subjects = [f'Exp{i+1}_Sample']

        try:
            n_points = int(input("Enter number of timepoints: "))
        except ValueError: n_points = 1
        
        try:
            reps = int(input("Enter number of replicates (2 or 3): "))
        except ValueError: reps = 2
        
        # Generator for this experiment
        for subj in subjects:
            subj_timepoints = []
            # Reversed timepoints as requested
            for t in range(n_points - 1, -1, -1):
                s_id = f"{subj}_t{t}" if n_points > 1 else subj
                subj_timepoints.append(s_id)
            
            # Append tuple: (list_of_ids, replicates)
            all_grouped_samples.append( (subj_timepoints, reps) )

    return all_grouped_samples

    return sample_ids, reps

def interactive_edit(layout):
    print("\n--- Review Layout ---")
    print("Available Commands:")
    print("  - view                     : Show current layout grid")
    print("  - change <Src> to <Dst>    : Move sample (e.g. 'change B5 to A5')")
    print("  - exclude <Row><Col>       : Clear well (e.g. 'exclude A4')")
    print("  - set <Row><Col> <Name>    : Set well value (e.g. 'set A5 Control')")
    print("  - done                     : Finish and Save")
    
    while True:
        cmd = input("Layout Command > ").strip()
        if cmd == 'done': break
        
        parts = cmd.split(' ', 2)
        action = parts[0].lower()
        
        if action == 'view':
            print(layout.get_layout().fillna('.'))
            
        elif action == 'change' and ' to ' in cmd:
            # Format: "change A3 to B3" - parts might be ['change', 'A3 to B3']
            # Re-split simpler
            try:
                # remove 'change '
                rest = cmd[7:].strip()
                src_str, dst_str = rest.split(' to ')
                src_str, dst_str = src_str.strip(), dst_str.strip()
                
                # Parse
                r_src, c_src = src_str[0].upper(), int(src_str[1:])
                r_dst, c_dst = dst_str[0].upper(), int(dst_str[1:])
                
                # Get Source
                val = layout.get_layout().at[r_src, c_src]
                type_val = layout.get_types().at[r_src, c_src]
                
                if pd.isna(val):
                     print(f"Source {src_str} is empty.")
                else:
                    # Move: Set Dest, Clear Source
                    layout.set_well(r_dst, c_dst, val, type_val)
                    layout.clear_well(r_src, c_src)
                    print(f"Moved {val} from {src_str} to {dst_str}")
            except Exception as e:
                print(f"Error moving well: {e}. Usage: change A3 to B3")

        elif action == 'exclude' and len(parts) >= 2:
            coord = parts[1]
            try:
                # Parse A3 -> Row A, Col 3
                r = coord[0].upper()
                c = int(coord[1:])
                layout.clear_well(r, c)
                print(f"Cleared {coord}")
            except:
                print("Invalid coordinate. Format: A3")

        elif action == 'set' and len(parts) >= 3:
            coord = parts[1]
            val = parts[2]
            try:
                r = coord[0].upper()
                c = int(coord[1:])
                layout.set_well(r, c, val, 'Sample')
                print(f"Set {coord} to {val}")
            except:
                print("Invalid format. Usage: set A3 MySample")
                
        else:
            print("Unknown command. Try 'view', 'exclude A3', 'set A3 Name', 'done'.")

def main():
    print("--- ELISA Layout Designer (Pre-Experiment) ---")
    
    # 1. Config
    grouped_samples_with_reps = get_user_config()
    
    # Standard Config
    # Plate 1: Full Standards (Col 1, 2)
    # Plate 2+: Partial Standards (Col 1 Only) - per user instruction
    
    plate_counter = 1
    current_samples = grouped_samples_with_reps
    
    while current_samples:
        print(f"\n--- Generating Plate {plate_counter} ---")
        
        # Standards Logic
        # PlateLayout now defaults to 1 Column of Standards (Col 1).
        layout = PlateLayout(standard_concentrations=[0, 0.1, 0.2, 0.4, 0.8, 1.6, 3.2, 6.4])
        
        # Assign Samples
        # Start at Col 2 (since Stds are only in Col 1)
        start_c = 2
        leftovers = layout.assign_samples(current_samples, start_col=start_c)
        
        # Save
        s_csv = f"plate_layout_p{plate_counter}.csv"
        s_png = f"plate_layout_p{plate_counter}.png"
        
        print(f"Saving Preview to '{s_png}'...")
        layout.to_csv(s_csv)
        layout.visualize_png(s_png)
        
        # Interactive Edit
        choice = input(f"Check '{s_png}'. Do you want to manually modify? (y/n): ").lower()
        if choice == 'y':
            interactive_edit(layout)
            print(f"Saving Final Layout (Plate {plate_counter})...")
            layout.to_csv(s_csv)
            layout.visualize_png(s_png)
            
        print(f"-> Plate {plate_counter} saved.")
        
        # Next Loop
        if not leftovers:
            break
            
        print(f"Overflow detected! {len(leftovers)} groups remaining. Creating Plate {plate_counter + 1}...")
        current_samples = leftovers
        plate_counter += 1
    
    print("\nDone! All samples processed.")

if __name__ == "__main__":
    main()
