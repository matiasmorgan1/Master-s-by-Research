import pandas as pd
import matplotlib.pyplot as plt
import os

# ===== USER SETTINGS =====
excel_file = r"C:\Users\jcch42\OneDrive - Durham University\Documents\Research Masters\Data Spreadsheets\MASTER_SPREADSHEET.xlsx"
output_folder = r"C:\Users\jcch42\OneDrive - Durham University\Documents\Research Masters\Figures\Master_Figures"
os.makedirs(output_folder, exist_ok=True)

# Height ratios (top to bottom)
# Old: [1, 0.4, 0.4, 0.4, 1, 1, 0.4, 0.4, 0.4]
# Now: split Surface Temp into two 0.5:0.5
height_ratios = [1, 0.4, 0.4, 0.4, 1, 0.5, 0.5, 0.4, 0.4, 0.4]  # total 10 rows

# ==========================

# Load Excel file
xls = pd.ExcelFile(excel_file)

for sheet in xls.sheet_names:
    print(f"Processing sheet: {sheet}")

    df = pd.read_excel(xls, sheet_name=sheet)

    # Clean column names
    df.columns = df.columns.str.strip().str.replace("–", "-", regex=False)

    # Convert Date column
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # Convert all other columns to numeric
    for col in df.columns:
        if col != "Date":
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Sort by date (important!)
    df = df.sort_values("Date")

    # Create figure with 10 axes (split surface temp)
    fig, axes = plt.subplots(
        nrows=10,
        ncols=1,
        figsize=(12, 18),
        sharex=True,
        gridspec_kw={'height_ratios': height_ratios}
    )

    fig.suptitle(sheet, fontsize=16, y=0.995)

    # Helper function (LINES ONLY)
    def safe_plot(ax, column_name):
        if column_name in df.columns:
            valid = df[["Date", column_name]].dropna()
            if not valid.empty:
                ax.plot(valid["Date"], valid[column_name])
        ax.grid(True)

    # 1) Terminus Retreat
    safe_plot(axes[0], "Terminus Retreat (m)")
    axes[0].set_ylabel("Retreat (m)")

    # 2–4) Velocities
    safe_plot(axes[1], "Velocity 1km down flowline (m/yr)")
    axes[1].set_ylabel("Vel 1km")
    safe_plot(axes[2], "Velocity 2km down flowline (m/yr)")
    axes[2].set_ylabel("Vel 2km")
    safe_plot(axes[3], "Velocity 5km down flowline (m/yr)")
    axes[3].set_ylabel("Vel 5km")

    # 5) Discharge
    safe_plot(axes[4], "Discharge Anomaly (Gt/yr)")
    axes[4].set_ylabel("Discharge")

    # 6–7) Surface Temp anomalies split into JJA and DJF
    safe_plot(axes[5], "Surface Temp Anomaly Summer JJA (°C)")
    axes[5].set_ylabel("Surface Temp JJA")
    safe_plot(axes[6], "Surface Temp Anomaly Winter DJF (°C)")
    axes[6].set_ylabel("Surface Temp DJF")

    # 8–10) Ocean Temps
    safe_plot(axes[7], "Ocean Temp Anomaly 50-100m")
    axes[7].set_ylabel("50-100m")
    safe_plot(axes[8], "Ocean Temp Anomaly 250-300m")
    axes[8].set_ylabel("250-300m")
    safe_plot(axes[9], "Ocean Temp Anomaly 450-500m")
    axes[9].set_ylabel("450-500m")

    axes[9].set_xlabel("Date")

    plt.tight_layout()
    plt.subplots_adjust(top=0.96)

    output_path = os.path.join(output_folder, f"{sheet}.png")
    plt.savefig(output_path, dpi=300)
    plt.close(fig)

print("All sheets processed.")
