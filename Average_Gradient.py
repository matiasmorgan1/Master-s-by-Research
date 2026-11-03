import pandas as pd

# File path
file_path = r"C:\Users\Matia\OneDrive - Durham University\Documents\Research Masters\Data Spreadsheets\Elevation\Elevation.xlsx"

# Load Excel file
df = pd.read_excel(file_path)

# Keep only first 5 km along the flowline
df_5km = df[df["Dist_Along_Flowline (m)"] <= 5000]

# Function to calculate gradient
def calc_gradient(group):
    group = group.sort_values("Dist_Along_Flowline (m)")
    
    x0 = group["Dist_Along_Flowline (m)"].iloc[0]
    x1 = group["Dist_Along_Flowline (m)"].iloc[-1]
    
    z0 = group["Elevation (m)"].iloc[0]
    z1 = group["Elevation (m)"].iloc[-1]
    
    gradient = (z1 - z0) / (x1 - x0)
    
    return pd.Series({
        "Distance_used_m": x1 - x0,
        "Elevation_change_m": z1 - z0,
        "Average_gradient": gradient
    })

# Calculate gradient for each glacier
results = df_5km.groupby("Glacier_ID").apply(calc_gradient).reset_index()

# Print results
print(results)

# Optional: save results
output_path = r"C:\Users\Matia\OneDrive - Durham University\Documents\Research Masters\Data Spreadsheets\Elevation\Glacier_Gradients_5km.xlsx"
results.to_excel(output_path, index=False)

print(f"\nResults saved to: {output_path}")
