# -*- coding: utf-8 -*-

import xarray as xr
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

# -----------------------
# User settings
# -----------------------
base_path = (
    r"C:\Users\jcch42\OneDrive - Durham University\Documents\Research Masters\Data"
    r"\Atmospheric_Data\MARv3.14.3-10km-daily-ERA5-{year}.nc"
)
out_path_jja = (
    r"C:\Users\jcch42\OneDrive - Durham University\Documents\Research Masters"
    r"\Figures\Atmospheric Temperature Change\MAR_JJA_TempAnomaly.png"
)
out_path_winter = (
    r"C:\Users\jcch42\OneDrive - Durham University\Documents\Research Masters"
    r"\Figures\Atmospheric Temperature Change\MAR_Winter_TempAnomaly.png"
)

years = range(1991, 2026)

glacier_coords = {
    226: (66.401121, -37.597138),
    284: (63.875912, -41.751149),
    303: (62.49107, -43.15229),
    320: (61.639677, -43.136743),
    323: (61.5672, -43.178178),
    245: (65.012344, -41.251558),
    286: (63.852942, -41.81786),
    296: (63.271613, -41.893431),
    233: (65.559332, -40.125435),
    238: (65.234993, -40.706336),
    232: (65.697643, -39.734977),
    300: (62.746836, -43.313508),
    304: (62.370736, -43.051618),
    310: (62.067368, -42.672088),
    270: (64.243946, -41.686908),
    335: (61.209418, -43.313418),
    297: (63.243014, -42.250839),
    298: (62.892129, -42.663693),
    281: (63.902382, -41.356373),
    293: (63.671452, -41.66253),
    224: (66.514517, -36.7617),
    239: (65.194252, -41.11792),
    227: (66.377318, -38.268088),
    258: (64.527037, -40.735331),
    266: (64.370986, -41.555998),
    302: (62.58016, -43.149846),
    330: (61.329731, -43.356673),
}

# -----------------------
# Load data and extract
# -----------------------
records = []

for year in years:
    path = base_path.format(year=year)
    if not os.path.exists(path):
        print(f"Missing file: {path}")
        continue

    print(f"Loading {year}")
    ds = xr.open_dataset(path)
    temp = ds["ST2"].sel(SECTOR=1) - 273.15
    LAT, LON = ds["LAT"], ds["LON"]

    for gid, (lat, lon) in glacier_coords.items():
        dist2 = (LAT - lat)**2 + (LON - lon)**2
        iy, ix = np.unravel_index(dist2.argmin(), dist2.shape)
        point = temp.isel(y=iy, x=ix).groupby("TIME.month").mean(dim="TIME")

        for month in point["month"].values:
            records.append({
                "glacier_id": gid,
                "lat": lat,
                "lon": lon,
                "year": year,
                "month": int(month),
                "temp": float(point.sel(month=month).values)
            })
    ds.close()

df = pd.DataFrame(records)

# -----------------------
# Order glaciers north → south
# -----------------------
lat_order = (
    pd.DataFrame.from_dict(glacier_coords, orient="index", columns=["lat", "lon"])
    .sort_values("lat", ascending=False)
)

# -----------------------
# MONTHLY anomalies relative to 2014 annual mean
# -----------------------
baseline_annual = (
    df[(df["year"] >= 1991) & (df["year"] <= 2011)]
    .groupby("glacier_id")["temp"]
    .mean()
)
df_monthly = df[df["year"] >= 2014].copy()
df_monthly["anomaly"] = df_monthly["temp"] - df_monthly["glacier_id"].map(baseline_annual)
df_monthly["time"] = pd.to_datetime(df_monthly["year"].astype(str) + "-" +
                                    df_monthly["month"].astype(str).str.zfill(2) + "-01")

heatmap_df = df_monthly.pivot(index="glacier_id", columns="time", values="anomaly")
heatmap_df = heatmap_df.loc[lat_order.index]

# -----------------------
# Export monthly anomaly heatmap data to Excel
# -----------------------
monthly_excel_path = (
    r"C:\Users\jcch42\OneDrive - Durham University\Documents\Research Masters"
    r"\Figures\Atmospheric Temperature Change\MAR_ST2_monthly_anomaly_heatmap.xlsx"
)

# Make columns human-readable (YYYY-MM)
monthly_export = heatmap_df.copy()
monthly_export.columns = [c.strftime("%Y-%m") for c in monthly_export.columns]

monthly_export.to_excel(
    monthly_excel_path,
    index_label="glacier_id"
)


# Explicitly compute min/max for plotting
data_to_plot = heatmap_df.values
vmin, vmax = np.nanmin(data_to_plot), np.nanmax(data_to_plot)

plt.figure(figsize=(14, 10))
plt.imshow(data_to_plot, aspect="auto", cmap="RdBu_r", vmin=vmin, vmax=vmax)
times = heatmap_df.columns
jan_positions = [i for i, t in enumerate(times) if t.month == 1]
jan_labels = [t.strftime("%m/%y") for t in times if t.month == 1]
plt.xticks(jan_positions, jan_labels, rotation=45)
plt.yticks(range(len(heatmap_df.index)), heatmap_df.index)
plt.colorbar(label="Temperature Anomaly (°C)")
plt.xlabel("Time (monthly)")
plt.ylabel("Glacier ID (South → North)")
plt.title("Monthly MAR ST2 Temperature Anomalies\nRelative to 1991-2011 Mean")
plt.tight_layout()
plt.savefig(
    r"C:\Users\jcch42\OneDrive - Durham University\Documents\Research Masters\Figures\Atmospheric Temperature Change\MAR_ST2_monthly_anomaly_heatmap.png",
    dpi=300, bbox_inches="tight"
)
plt.show()

# -----------------------
# JJA anomalies relative to 2014 JJA mean
# -----------------------
jja_months = [6, 7, 8]
baseline_jja = (
    df[(df["year"] >= 1991) & (df["year"] <= 2011)]
    .query("month in @jja_months")
    .groupby("glacier_id")["temp"]
    .mean()
)

df_jja = df[df["month"].isin(jja_months) & (df["year"] >= 2013)].copy()
df_jja["anomaly"] = df_jja["temp"] - df_jja["glacier_id"].map(baseline_jja)

jja_annual = df_jja.groupby(["glacier_id", "year"])["anomaly"].mean().unstack("year")
jja_annual = jja_annual.loc[lat_order.index]
jja_annual.columns = jja_annual.columns.astype(int)

# -----------------------
# Export JJA anomaly data to Excel
# -----------------------
jja_excel_path = (
    r"C:\Users\jcch42\OneDrive - Durham University\Documents\Research Masters"
    r"\Figures\Atmospheric Temperature Change\MAR_JJA_TempAnomaly.xlsx"
)

jja_annual.to_excel(
    jja_excel_path,
    index_label="glacier_id"
)


data_to_plot = jja_annual.values
vmin, vmax = np.nanmin(data_to_plot), np.nanmax(data_to_plot)

plt.figure(figsize=(14, 10))
plt.imshow(data_to_plot, aspect="auto", cmap="RdBu_r", vmin=vmin, vmax=vmax)
plt.xticks(range(len(jja_annual.columns)), jja_annual.columns, rotation=45)
plt.yticks(range(len(jja_annual.index)), jja_annual.index)
plt.colorbar(label="JJA Temperature Anomaly (°C)")
plt.xlabel("Year")
plt.ylabel("Glacier ID (South → North)")
plt.title("JJA MAR ST2 Temperature Anomalies\nRelative to 1991-2011 JJA Mean")
plt.tight_layout()
plt.savefig(out_path_jja, dpi=300, bbox_inches="tight")
plt.show()

# -----------------------
# Prepare winter data (DJF)
# -----------------------
df_winter = df[df["month"].isin([12, 1, 2])].copy()

# Assign winter_year: Dec belongs to next year's winter
df_winter.loc[df_winter["month"] == 12, "winter_year"] = df_winter["year"] + 1
df_winter.loc[df_winter["month"].isin([1, 2]), "winter_year"] = df_winter["year"]

# Baseline: 2014/15 winter (Dec 2014 + Jan 2015 + Feb 2015)
df_winter_baseline = df[df["month"].isin([12, 1, 2])].copy()

# Assign winter_year for baseline period
df_winter_baseline.loc[df_winter_baseline["month"] == 12, "winter_year"] = df_winter_baseline["year"] + 1
df_winter_baseline.loc[df_winter_baseline["month"].isin([1, 2]), "winter_year"] = df_winter_baseline["year"]

# Select baseline winters 1991–2011
df_winter_baseline = df_winter_baseline[
    (df_winter_baseline["winter_year"] >= 1991) &
    (df_winter_baseline["winter_year"] <= 2011)
]

baseline_winter = (
    df_winter_baseline
    .groupby("glacier_id")["temp"]
    .mean()
)


# Filter data for winters 2015/16 onward
df_winter = df_winter[df_winter["winter_year"] >= 2014].copy()

# Compute anomalies
df_winter["anomaly"] = df_winter["temp"] - df_winter["glacier_id"].map(baseline_winter)

# Average DJF months per glacier × winter_year
winter_annual = df_winter.groupby(["glacier_id", "winter_year"])["anomaly"].mean().unstack("winter_year")

# Keep glaciers north → south
winter_annual = winter_annual.loc[lat_order.index]

# Fix column type to integer
winter_annual.columns = winter_annual.columns.astype(int)

# Create DJF labels
winter_labels = [f"DJF{y-1}/{y}" for y in winter_annual.columns]

# -----------------------
# Export winter (DJF) anomaly data to Excel
# -----------------------
winter_excel_path = (
    r"C:\Users\jcch42\OneDrive - Durham University\Documents\Research Masters"
    r"\Figures\Atmospheric Temperature Change\MAR_Winter_TempAnomaly.xlsx"
)

# Use DJF labels as column names
winter_export = winter_annual.copy()
winter_export.columns = winter_labels

winter_export.to_excel(
    winter_excel_path,
    index_label="glacier_id"
)


# Compute full data min/max for color scaling
vmax_abs_winter = np.nanmax(np.abs(winter_annual.values))

# Plot
plt.figure(figsize=(14, 10))
plt.imshow(
    winter_annual.values,
    aspect="auto",
    cmap="RdBu_r",
    vmin=-vmax_abs_winter,
    vmax=vmax_abs_winter
)
plt.xticks(range(len(winter_annual.columns)), winter_labels, rotation=45)
plt.yticks(range(len(winter_annual.index)), winter_annual.index)
plt.colorbar(label="Winter (DJF) Temperature Anomaly (°C)")
plt.xlabel("Winter Year (DJF)")
plt.ylabel("Glacier ID (South → North)")
plt.title("Winter (DJF) MAR ST2 Temperature Anomalies\nRelative to 1991-2011 Winter Mean")
plt.tight_layout()
plt.savefig(out_path_winter, dpi=300, bbox_inches="tight")
plt.show()


