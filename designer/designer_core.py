import pandas as pd
import numpy as np

# Constants
COLS = 8
ROWS = 12
COL_LABELS = [chr(i) for i in range(ord('A') + COLS - 1, ord('A') - 1, -1)]
ROW_LABELS = [str(i + 1) for i in range(ROWS)]

def grid_to_dataframe(grid_data, subject_names_dict):
    """
    Converts grid dictionary to DataFrame for export.
    
    Parameters:
    - grid_data (dict): Mapping (col, row) -> cell_dict
    - subject_names_dict (dict): Mapping (exp, subj) -> name_string
    
    Returns:
    - pd.DataFrame: Formatted for CSV export.
    """
    data_rows = []
    for r in range(ROWS):
        for c in range(COLS):
            cell = grid_data.get((c, r))
            row_label = ROW_LABELS[r]
            col_label = COL_LABELS[c]
            well_id = f"{col_label}{row_label}"
            
            if cell:
                c_type = cell['type']
                if c_type == 'CAL':
                    data_rows.append({
                        'Well': well_id, 'Type': 'Calibration', 
                        'Concentration': cell['conc'], 
                        'Experiment': '', 'Subject': '', 'Timepoint': '', 'Replicate': '',
                        'Subject Name': ''
                    })
                else:
                    exp = cell['exp']
                    subj = cell['subj']
                    # Handle subject name lookup safely
                    subj_name = subject_names_dict.get((exp, subj), '')
                    
                    data_rows.append({
                        'Well': well_id, 'Type': 'Experiment',
                        'Concentration': '',
                        'Experiment': exp,
                        'Subject': subj,
                        'Timepoint': f"t{cell['samp']}",
                        'Replicate': cell['rep'],
                        'Subject Name': subj_name
                    })
            else:
                data_rows.append({
                    'Well': well_id, 'Type': 'Empty', 
                    'Concentration': '', 'Experiment': '', 'Subject': '', 'Timepoint': '', 'Replicate': '',
                    'Subject Name': ''
                })
    
    return pd.DataFrame(data_rows)

def dataframe_to_grid(df):
    """
    Parses imported DataFrame into grid structure.
    
    Returns:
    - tuple: (grid_data, subject_names_dict, max_counters)
    """
    grid_data = {}
    subject_names = {}
    max_exp = 0
    
    for _, row in df.iterrows():
        well = str(row['Well'])
        if len(well) < 2: continue
        
        col_char = well[0]
        row_str = well[1:]
        
        if col_char in COL_LABELS:
            c = COL_LABELS.index(col_char)
        else:
            continue
            
        try:
            r = int(row_str) - 1
        except:
            continue
            
        if 0 <= c < COLS and 0 <= r < ROWS:
            t = str(row['Type'])
            if t == 'Calibration':
                try:
                    conc = float(row['Concentration'])
                except:
                    conc = 0.0
                grid_data[(c, r)] = {
                    'type': 'CAL',
                    'conc': conc
                }
            elif t == 'Experiment':
                 try:
                     exp = int(row['Experiment'])
                     subj = int(row['Subject'])
                     
                     tp_str = str(row['Timepoint'])
                     if tp_str.lower().startswith('t'):
                         samp = int(tp_str[1:])
                     else:
                         samp = int(float(tp_str))
                         
                     rep = int(row['Replicate'])
                 except:
                     continue # Skip malformed rows
                 
                 # Name
                 name = str(row.get('Subject Name', ''))
                 if name.lower() == 'nan': name = ''
                 
                 if (exp, subj) not in subject_names and name:
                     subject_names[(exp, subj)] = name
                 
                 grid_data[(c, r)] = {
                     'type': 'EXP',
                     'exp': exp,
                     'subj': subj,
                     'samp': samp,
                     'rep': rep
                 }
                 if exp > max_exp: max_exp = exp

    # Recalculate State Logic
    current_exp = max(1, max_exp)
    
    # helper logic to find max subj/samp
    max_subj = 0
    for cell in grid_data.values():
        if cell.get('type') == 'EXP' and cell['exp'] == current_exp:
            if cell['subj'] > max_subj: max_subj = cell['subj']
            
    current_subj = max_subj if max_subj > 0 else 1
    
    max_samp = 0
    subj_has_cells = False
    for cell in grid_data.values():
         if cell.get('type') == 'EXP' and cell['exp'] == current_exp and cell['subj'] == current_subj:
             subj_has_cells = True
             if cell['samp'] > max_samp: max_samp = cell['samp']
             
    next_samp = max_samp + 1 if subj_has_cells else 0
    
    state = {
        'current_exp': current_exp,
        'current_subj': current_subj,
        'next_sample_id': next_samp
    }
    
    return grid_data, subject_names, state

def fill_cells(c1, r1, c2, r2, current_exp, current_subj, next_sample_id, orientation):
    """
    Generates cell data for a selected range based on orientation.
    Returns:
    - dict: partial grid updates {(c, r): cell_dict}
    - int: updated next_sample_id
    """
    updates = {}
    local_samp_id = next_sample_id
    
    # Validate Ranges
    c1, c2 = min(c1, c2), max(c1, c2)
    r1, r2 = min(r1, r2), max(r1, r2)
    
    if orientation == 'vertical':
        # Cols define samples
        for c in range(c1, c2 + 1):
            s_id = local_samp_id
            local_samp_id += 1
            rep_count = 1
            for r in range(r1, r2 + 1):
               updates[(c, r)] = {
                    'type': 'EXP',
                    'exp': current_exp,
                    'subj': current_subj,
                    'samp': s_id,
                    'rep': rep_count
               }
               rep_count += 1
    else:
        # Rows define samples
        for r in range(r1, r2 + 1):
            s_id = local_samp_id
            local_samp_id += 1
            rep_count = 1
            for c in range(c1, c2 + 1):
                updates[(c, r)] = {
                    'type': 'EXP',
                    'exp': current_exp,
                    'subj': current_subj,
                    'samp': s_id,
                    'rep': rep_count
               }
                rep_count += 1
                
    return updates, local_samp_id
