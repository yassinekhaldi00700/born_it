import pandas as pd
import re

file1 = r"C:\Users\DELL\Downloads\10-10-2025 08-1130-1.xlsx"
file2 = r"C:\Users\DELL\OneDrive - Université EuroMed de Fès (UEMF)\Desktop\users.csv"

# Read both files
df1 = pd.read_excel(file1) if file1.endswith('.xlsx') else pd.read_csv(file1)
# Fix CSV reading for semicolon-separated file
df2 = pd.read_csv(file2, sep=';') if file2.endswith('.csv') else pd.read_excel(file2)

# Clean column names: remove spaces, invisible chars, lowercase for safety
df1.columns = df1.columns.str.strip().str.replace('\ufeff', '').str.lower()
df2.columns = df2.columns.str.strip().str.replace('\ufeff', '').str.lower()

print("✅ Columns in first file:", df1.columns.tolist())   # Debug
print("✅ Columns in second file:", df2.columns.tolist())  # Debug
print("✅ Sample data from second file:")
print(df2.head())  # Show sample data

# Extract numeric ID from 'utilisateur'
df1['id'] = df1['utilisateur'].apply(lambda x: int(re.search(r'\d+', str(x)).group()) if pd.notnull(x) and re.search(r'\d+', str(x)) else None)

print("✅ Sample extracted IDs:", df1['id'].head().tolist())  # Debug extracted IDs

# Make sure 'usrid' exists (auto-detect if similar)
possible_usrid_cols = [c for c in df2.columns if 'usr' in c.lower() and 'id' in c.lower()]
if possible_usrid_cols:
    usr_col = possible_usrid_cols[0]
    print(f"✅ Found user ID column: {usr_col}")
else:
    raise KeyError("❌ No column similar to 'USRUID' found in second file.")

# Fix data type mismatch before merging
df1['id'] = df1['id'].astype(str)
df2[usr_col] = df2[usr_col].astype(str)

# Merge dataframes
merged = pd.merge(df1, df2, left_on='id', right_on=usr_col, how='left')

print("✅ Merge completed. Shape:", merged.shape)
print("✅ Sample merged data:")
print(merged[['id', usr_col]].head())  # Show merge results

# Rename VAL → Matricule if exists
print("✅ Available columns after merge:", merged.columns.tolist())  # Debug
if 'val' in merged.columns:
    merged.rename(columns={'val': 'matricule'}, inplace=True)
    print("✅ Renamed 'val' to 'matricule'")
else:
    # Try to find any column that might contain matricule data
    possible_matricule_cols = [c for c in merged.columns if 'val' in c or 'matricule' in c or 'mat' in c]
    if possible_matricule_cols:
        merged.rename(columns={possible_matricule_cols[0]: 'matricule'}, inplace=True)
        print(f"✅ Found and renamed '{possible_matricule_cols[0]}' to 'matricule'")
    else:
        merged['matricule'] = None  # in case it's missing
        print("❌ No matricule column found, setting to None")

# Keep only main columns (if exist)
final_cols = [c for c in ['date', 'utilisateur', 'groupe utilisateur', 'equipement', 'matricule'] if c in merged.columns]
merged = merged[final_cols]

# Save to Excel
import datetime
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = rf"C:\Users\DELL\Downloads\merged_output_{timestamp}.xlsx"
try:
    merged.to_excel(output_file, index=False)
    print(f"✅ File saved successfully to: {output_file}")
except PermissionError:
    # If permission denied, try saving to Desktop
    output_file = rf"C:\Users\DELL\Desktop\merged_output_{timestamp}.xlsx"
    merged.to_excel(output_file, index=False)
    print(f"✅ File saved to Desktop: {output_file}")
