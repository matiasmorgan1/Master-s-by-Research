# This loads locally-downloaded MAR data (NetCDF), and, for coordinates listed, computes time-series temperature anomaly for 2014-2026 using a 1991-2011 baseline.
# This is then saved as an excel spreadsheet.

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
