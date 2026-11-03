import pandas as pd

# ==============================
# File paths
# ==============================
input_path = r"C:\Users\jcch42\OneDrive - Durham University\Documents\Research Masters\Data Spreadsheets\MASTER_SPREADSHEET.xlsx"
output_path = r"C:\Users\jcch42\OneDrive - Durham University\Documents\Research Masters\Data Spreadsheets\MASTER_SPREADSHEET_SEASONAL.xlsx"

# ==============================
# Season helper functions
# ==============================
def assign_season(month):
    if month in [12, 1, 2]:
        return "DJF"
    elif month in [3, 4, 5]:
        return "MAM"
    elif month in [6, 7, 8]:
        return "JJA"
    else:
        return "SON"

def season_middle_month(season):
    return {
        "DJF": 1,
        "MAM": 4,
        "JJA": 7,
        "SON": 10
    }[season]

# ==============================
# Read workbook
# ==============================
xls = pd.ExcelFile(input_path)

with pd.ExcelWriter(output_path, engine="openpyxl") as writer:

    for sheet in xls.sheet_names:
        print(f"Processing: {sheet}")
        
        df = pd.read_excel(xls, sheet_name=sheet)
        df["Date"] = pd.to_datetime(df["Date"])

        # Identify relevant columns
        discharge_col = "Discharge Anomaly (Gt/yr)"
        surface_col = "Surface temp Anomaly (°C)"
        ocean_cols = [col for col in df.columns if "Ocean Temp" in col]

        selected_cols = ["Date", discharge_col, surface_col] + ocean_cols
        df = df[selected_cols]

        # Add time components
        df["Month"] = df["Date"].dt.month
        df["Year"] = df["Date"].dt.year
        df["Season"] = df["Month"].apply(assign_season)

        # Fix DJF year (December belongs to next year's winter)
        df.loc[(df["Season"] == "DJF") & (df["Month"] == 12), "Year"] += 1

        # Compute seasonal means
        seasonal = (
            df.groupby(["Year", "Season"])
            .mean(numeric_only=True)
            .reset_index()
        )

        # Create seasonal date
        seasonal["Date"] = pd.to_datetime(
            dict(
                year=seasonal["Year"],
                month=seasonal["Season"].map(season_middle_month),
                day=1
            )
        )

        # Reorder columns
        seasonal = seasonal.sort_values("Date")
        seasonal = seasonal.drop(columns=["Year"])

        # Save sheet
        seasonal.to_excel(writer, sheet_name=sheet, index=False)

print("Seasonal spreadsheet successfully created.")
