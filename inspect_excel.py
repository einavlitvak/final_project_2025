import openpyxl
import os

file_path = "insulin ELISA ELC1-10 c21 control day 2 + EL196-199 Sweetener 23.5.25.xlsx"
abs_path = os.path.abspath(file_path)

print(f"Reading: {abs_path}")

try:
    wb = openpyxl.load_workbook(abs_path, data_only=True)
    sheet = wb.active
    
    # Print Rows 20-60
    print("\n--- Rows 20-60 ---")
    for row in range(20, 61):
        row_values = []
        for col in range(1, 14): # Read first 13 cols
            val = sheet.cell(row=row, column=col).value
            # formatting to keep it compact
            if val is None: s = ""
            elif isinstance(val, (int, float)): s = f"{val:.3f}"
            else: s = str(val)[:10]
            row_values.append(s)
        print(f"Row {row}: {', '.join(row_values)}")

except Exception as e:
    print(f"Error: {e}")
