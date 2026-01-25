import pandas as pd
import numpy as np
from scipy import stats
import itertools

def extract_grid(full_df, start_row):
    """
    Extracts an 8x12 grid from the dataframe starting at start_row.
    
    Parameters:
    - full_df (pd.DataFrame): The raw dataframe from the excel file.
    - start_row (int): The index where the grid starts (the row with 'A', 'B' etc.).
    
    Returns:
    - pd.DataFrame: Dataframe with columns ['Well', 'OD'].
    """
    data = []
    for r in range(8): # 8 Rows A-H
        row_idx = start_row + r
        # Row Label (A, B, C...)
        if row_idx >= len(full_df): break
        row_label = str(full_df.iloc[row_idx, 0]).strip()
        
        # Data values at cols 1 to 12
        values = full_df.iloc[row_idx, 1:13].values
        
        for c, val in enumerate(values):
            col_label = str(c + 1)
            well_id = f"{row_label}{col_label}"
            try:
                val = float(val)
            except:
                val = np.nan
            data.append({'Well': well_id, 'OD': val})
            
    return pd.DataFrame(data)

def parse_tecan_excel(path):
    """
    Parses Tecan Excel output to extract OD450 and OD630 grids.
    
    Parameters:
    - path (str): Path to the Excel/CSV file.
    
    Returns:
    - tuple: (od450_df, od630_df) both as DataFrames with ['Well', 'OD'].
    
    Raises:
    - ValueError: If grids cannot be identified.
    """
    df = pd.read_csv(path, sep=None, engine='python', header=None) if path.endswith('.csv') else pd.read_excel(path, header=None)
    
    # Find start of plate grids (marked by '<>')
    grid_starts = df.index[df.iloc[:, 0] == '<>'].tolist()
    
    if len(grid_starts) < 2:
        raise ValueError("Could not find two data blocks starting with '<>' (need 450nm and 630nm).")
        
    od450_df = extract_grid(df, grid_starts[0] + 1)
    od630_df = extract_grid(df, grid_starts[1] + 1)
    
    return od450_df, od630_df

def merge_and_correct(layout_df, od450_df, od630_df):
    """
    Merges Layout with OD data and calculates corrected OD.
    
    Parameters:
    - layout_df (pd.DataFrame): Layout data.
    - od450_df (pd.DataFrame): Data from 450nm.
    - od630_df (pd.DataFrame): Data from 630nm.
    
    Returns:
    - pd.DataFrame: Merged dataframe with 'OD_Corr' column.
    """
    od_df = pd.merge(od450_df, od630_df, on='Well', suffixes=('_450', '_630'))
    od_df['OD_Corr'] = od_df['OD_450'] - od_df['OD_630']
    
    merged_df = pd.merge(layout_df, od_df, on='Well', how='left')
    return merged_df

def fit_calibration_model(df):
    """
    Fits a linear regression model to the Calibration standards.
    
    Parameters:
    - df (pd.DataFrame): The full merged dataframe.
    
    Returns:
    - dict: {'slope', 'intercept', 'r_squared'} of the model.
    - pd.DataFrame: The mean ODs per concentration (for plotting).
    """
    cal_data = df[df['Type'] == 'Calibration'].copy()
    if cal_data.empty:
        return None, None
        
    cal_means = cal_data.groupby('Concentration')['OD_Corr'].mean().reset_index()
    
    slope, intercept, r_value, p_value, std_err = stats.linregress(cal_means['Concentration'], cal_means['OD_Corr'])
    
    model = {
        'slope': slope,
        'intercept': intercept,
        'r_squared': r_value**2
    }
    return model, cal_means

def calculate_concentrations(df, model):
    """
    Calculates concentrations for Unknowns using the calibration model.
    
    Parameters:
    - df (pd.DataFrame): Dataframe with 'Type' and 'OD_Corr'.
    - model (dict): The calibration model.
    
    Returns:
    - pd.DataFrame: Dataframe with new 'Calculated_Conc' column.
    """
    if not model or model['slope'] == 0:
        df['Calculated_Conc'] = np.nan
        return df

    def get_conc(row):
        if row['Type'] == 'Experiment':
            return (row['OD_Corr'] - model['intercept']) / model['slope']
        return row['Concentration']

    df['Calculated_Conc'] = df.apply(get_conc, axis=1)
    return df

def run_statistical_analysis(exp_df, config):
    """
    Runs statistical tests based on configuration.
    
    Parameters:
    - exp_df (pd.DataFrame): Experiment data.
    - config (dict): {'timepoints': [], 'paired': bool, 'tails': str, 'posthoc': bool}
    
    Returns:
    - dict: Results containing 'p_value', 'test_decision', 'shapiro', 'p_levene', 'posthoc', 'High_CV'.
    """
    results = {}
    
    # 1. Clean Subject Names
    exp_df['Subject Name'] = exp_df['Subject Name'].fillna('')
    exp_df['Subject Name'] = exp_df.apply(
        lambda row: f"Subject {int(row['Subject'])}" if str(row['Subject Name']).strip() == '' or str(row['Subject Name']).lower() == 'nan' else row['Subject Name'], 
        axis=1
    )
    
    # 2. CV Calculation
    grouped = exp_df.groupby(['Subject', 'Subject Name', 'Timepoint'])['Calculated_Conc'].agg(['mean', 'std', 'count']).reset_index()
    grouped['CV_Percent'] = (grouped['std'] / grouped['mean']) * 100
    
    high_cv = grouped[grouped['CV_Percent'] > 20]
    if not high_cv.empty:
        results['High_CV'] = high_cv
        
    # 3. Pivot for Testing
    pivoted = grouped.pivot(index='Subject Name', columns='Timepoint', values='mean')
    
    selected_tps = config['timepoints']
    valid_tps = [tp for tp in selected_tps if tp in pivoted.columns]
    
    if len(valid_tps) < 2: return results # Not enough data
    
    if config['paired']:
        clean_data = pivoted[valid_tps].dropna()
        arrays = [clean_data[tp] for tp in valid_tps]
    else:
        arrays = [pivoted[tp].dropna() for tp in valid_tps]
        
    if any(len(arr) < 3 for arr in arrays): return results # Too few samples
    
    # 4. Normality & Homogeneity
    normality_passed = True
    shapiro_results = {}
    for tp, arr in zip(valid_tps, arrays):
        if len(arr) >= 3:
            _, p = stats.shapiro(arr)
            shapiro_results[tp] = p
            if p < 0.05: normality_passed = False
        else:
             shapiro_results[tp] = np.nan
    results['shapiro'] = shapiro_results
    
    try:
        _, p_levene = stats.levene(*arrays)
        results['p_levene'] = p_levene
        homogeneity_passed = p_levene > 0.05
    except:
        results['p_levene'] = np.nan
        homogeneity_passed = True
        
    # 5. Decision Logic
    p_val = np.nan
    decision = "Uncertain"
    tails = config.get('tails', 'two-sided')
    
    if len(valid_tps) == 2:
        if normality_passed:
            if config['paired']:
                decision = "Paired T-Test"
                _, p_val = stats.ttest_rel(arrays[0], arrays[1], alternative=tails)
            else:
                decision = "Unpaired T-Test"
                _, p_val = stats.ttest_ind(arrays[0], arrays[1], alternative=tails)
        else:
            if config['paired']:
                decision = "Wilcoxon Signed-Rank"
                _, p_val = stats.wilcoxon(arrays[0], arrays[1], alternative=tails)
            else:
                decision = "Mann-Whitney U"
                _, p_val = stats.mannwhitneyu(arrays[0], arrays[1], alternative=tails)
    else:
        # > 2 Groups
        if normality_passed and homogeneity_passed:
            if config['paired']:
                decision = "Repeated Measures (Friedman)" # Fallback as scipy lacks RM ANOVA
                _, p_val = stats.friedmanchisquare(*arrays)
            else:
                decision = "ANOVA (One-Way)"
                _, p_val = stats.f_oneway(*arrays)
        else:
             if config['paired']:
                decision = "Friedman Chi-Square"
                _, p_val = stats.friedmanchisquare(*arrays)
             else:
                decision = "Kruskal-Wallis"
                _, p_val = stats.kruskal(*arrays)
                
    results['p_value'] = p_val
    results['test_decision'] = decision
    
    # 6. Post-Hoc
    if config['posthoc'] and p_val < 0.05:
        posthoc_res = []
        combinations = list(itertools.combinations(enumerate(valid_tps), 2))
        alpha_corrected = 0.05 / len(combinations)
        
        for (idx1, name1), (idx2, name2) in combinations:
            arr1 = arrays[idx1]
            arr2 = arrays[idx2]
            
            ph_test = ""
            ph_p = 1.0
            
            if "T-Test" in decision or "ANOVA" in decision:
                if config['paired']:
                     ph_test = "Paired T-Test"
                     _, ph_p = stats.ttest_rel(arr1, arr2)
                else:
                     ph_test = "Unpaired T-Test"
                     _, ph_p = stats.ttest_ind(arr1, arr2)
            else:
                 if config['paired']:
                     ph_test = "Wilcoxon"
                     _, ph_p = stats.wilcoxon(arr1, arr2)
                 else:
                     ph_test = "Mann-Whitney"
                     _, ph_p = stats.mannwhitneyu(arr1, arr2)
            
            sig = "*" if ph_p < alpha_corrected else "ns"
            posthoc_res.append({
                'Comparison': f"{name1} vs {name2}",
                'Test': ph_test,
                'P-Value': ph_p,
                'Sig (Bonf)': sig
            })
            
        results['posthoc'] = pd.DataFrame(posthoc_res)
        
    return results
