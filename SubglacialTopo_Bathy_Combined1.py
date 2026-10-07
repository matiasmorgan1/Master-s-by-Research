import os
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

# ============================================================
# 1. USER SETTINGS & FILE PATHS (LOCAL WINDOWS ENVIRONMENT)
# ============================================================
topo_file = r"C:\Users\Matia\OneDrive - Durham University\Documents\Research Masters\Data Spreadsheets\Subglacial Topography\Subglacial Topography.xlsx"
bathy_file = r"C:\Users\Matia\OneDrive - Durham University\Documents\Research Masters\Data Spreadsheets\Bathymetry\Bathymetry_Data.xlsx"
output_dir = r"C:\Users\Matia\OneDrive - Durham University\Documents\Research Masters\Figures\Combined_Profiles"

max_topo_limit = 5000  # m left of terminus
grid_spacing = 10  # m for mean interpolation

# IDs to exclude from topography to avoid plotting/calculating duplicate profiles
topo_excluded_ids = {286, 323}

# ============================================================
# 2. DEFINITIONS & MAPPING (UPDATED FOR 6 CLUSTERS)
# ============================================================
cluster_dict = {
    # Cluster 1 (10 glaciers)
    232: 1,
    245: 1,
    296: 1,
    266: 1,
    284: 1,  # (286 omitted in favor of 284)
    293: 1,
    304: 1,
    300: 1,
    335: 1,
    310: 1,
    # Cluster 2 (6 glaciers)
    303: 2,
    320: 2,  # (323 omitted in favor of 320)
    302: 2,
    330: 2,
    281: 2,
    258: 2,
    # Cluster 3 (2 glaciers)
    298: 3,
    297: 3,
    # Cluster 4 (2 glaciers)
    233: 4,
    224: 4,
    # Cluster 5 (2 glaciers)
    227: 5,
    226: 5,
    # Cluster 6 (3 glaciers)
    238: 6,
    239: 6,
    270: 6,
}

id_translation = {
    "1": [224],
    "2": [226],
    "3": [227],
    "4": [232],
    "5": [233],
    "6": [238],
    "7": [239],
    "8": [245],
    "9": [258],
    "10": [266],
    "11": [270],
    "12": [281],
    "13": [296],
    "14": [297],
    "15": [298],
    "16": [300],
    "17": [302],
    "18": [303],
    "19": [304],
    "20": [310],
    "21": [320, 323],
    "22": [284, 286],
    "23": [330],
    "24": [335],
    "25": [293],
}

group_colors = {
    1: "#4776EE",
    2: "#1BD0D5",
    3: "#61FC6C",
    4: "#D2E935",
    5: "#FE9B2D",
    6: "#DA3907",
}

os.makedirs(output_dir, exist_ok=True)

# ============================================================
# 3. LOADING & PRE-PROCESSING DATASET A: TOPOGRAPHY (LEFT SIDE)
# ============================================================
df_topo_raw = pd.read_excel(topo_file)
df_topo_raw = df_topo_raw.rename(
    columns={
        "Distance along Flowline (m)": "dist",
        "Elevation (m)": "elev",
        "ID": "id",
    }
)
real_glacier_ids = [
    224,
    226,
    227,
    232,
    233,
    238,
    239,
    245,
    258,
    266,
    270,
    281,
    284,
    286,
    293,
    296,
    297,
    298,
    300,
    302,
    303,
    304,
    310,
    320,
    323,
    330,
    335,
]
spreadsheet_ids = sorted(df_topo_raw["id"].unique())
id_mapping = dict(zip(spreadsheet_ids, real_glacier_ids))
df_topo_raw["real_id"] = df_topo_raw["id"].map(id_mapping)
df_topo_raw["cluster"] = df_topo_raw["real_id"].map(cluster_dict)

# EXCLUDE 286 and 323 from topography DataFrame
df_topo = (
    df_topo_raw[
        (df_topo_raw["dist"] <= max_topo_limit)
        & (~df_topo_raw["real_id"].isin(topo_excluded_ids))
    ]
    .dropna(subset=["cluster"])
    .copy()
)

# ============================================================
# 4. LOADING & PRE-PROCESSING DATASET B: BATHYMETRY (RIGHT SIDE)
# ============================================================
df_bathy_raw = pd.read_excel(bathy_file)
df_bathy_raw = df_bathy_raw.rename(
    columns={
        df_bathy_raw.columns[1]: "Raw_ID",
        df_bathy_raw.columns[2]: "Distance",
        df_bathy_raw.columns[3]: "Depth",
    }
)
df_bathy_raw["Distance"] = pd.to_numeric(
    df_bathy_raw["Distance"], errors="coerce"
)
df_bathy_raw["Depth"] = pd.to_numeric(df_bathy_raw["Depth"], errors="coerce")
df_bathy_raw = df_bathy_raw.dropna(subset=["Raw_ID", "Distance", "Depth"])

bathy_processed = []
for raw_key, real_ids in id_translation.items():
  subset = df_bathy_raw[
      df_bathy_raw["Raw_ID"].astype(str).str.strip() == str(raw_key)
  ].copy()
  for rid in real_ids:
    if rid in cluster_dict:
      g_subset = subset.copy()
      g_subset["real_id"] = rid
      g_subset["cluster"] = cluster_dict[rid]
      bathy_processed.append(g_subset)

df_bathy = (
    pd.concat(bathy_processed, ignore_index=True)
    if bathy_processed
    else pd.DataFrame()
)

# Find the absolute shortest maximum distance among all tracked glaciers
shortest_bathy_limit = 9999999.0
for gid in cluster_dict.keys():
  g_bathy_check = df_bathy[df_bathy["real_id"] == gid]
  if not g_bathy_check.empty:
    g_max = g_bathy_check["Distance"].max()
    if g_max < shortest_bathy_limit:
      shortest_bathy_limit = g_max

# Safeguard fallback if data structure is empty
if shortest_bathy_limit == 9999999.0:
  shortest_bathy_limit = 5000.0

# ============================================================
# 5. PLOTTING WITH SPLIT X-AXES USING GRIDSPEC
# ============================================================
clusters_to_plot = sorted(list(set(cluster_dict.values())))
n_clusters = len(clusters_to_plot)

fig = plt.figure(figsize=(12, 2.5 * n_clusters))

gs = gridspec.GridSpec(n_clusters, 2, figure=fig, wspace=0.08, hspace=0.35)

for i, cluster in enumerate(clusters_to_plot):
  ax_left = fig.add_subplot(gs[i, 0])
  ax_right = fig.add_subplot(gs[i, 1])

  base_color = group_colors.get(cluster, "tab:grey")

  c_topo = df_topo[df_topo["cluster"] == cluster]
  c_bathy = (
      df_bathy[df_bathy["cluster"] == cluster]
      if not df_bathy.empty
      else pd.DataFrame()
  )

  # Full list for bathymetry vs. filtered list for topography
  all_glaciers_in_cluster = sorted(
      [gid for gid, c in cluster_dict.items() if c == cluster]
  )
  topo_glaciers_in_cluster = [
      gid for gid in all_glaciers_in_cluster if gid not in topo_excluded_ids
  ]

  topo_means_list, bathy_means_list = [], []
  max_topo_seen = 0

  # Baseline markers at y=0
  ax_left.axhline(
      0, color="black", linestyle="-", linewidth=0.8, alpha=0.3, zorder=1
  )
  ax_right.axhline(
      0, color="black", linestyle="-", linewidth=0.8, alpha=0.3, zorder=1
  )

  # PLOT INDIVIDUAL TOPOGRAPHY PROFILES (EXCLUDING SHARED DUPES)
  for gid in topo_glaciers_in_cluster:
    g_topo = c_topo[c_topo["real_id"] == gid].sort_values("dist")
    if not g_topo.empty:
      ax_left.plot(
          -g_topo["dist"] / 1000,
          g_topo["elev"],
          color=base_color,
          alpha=0.35,
          linewidth=0.8,
          zorder=2,
      )
      max_topo_seen = max(max_topo_seen, g_topo["dist"].max())

  # PLOT INDIVIDUAL BATHYMETRY PROFILES
  for gid in all_glaciers_in_cluster:
    g_bathy = (
        c_bathy[c_bathy["real_id"] == gid].sort_values("Distance")
        if not c_bathy.empty
        else pd.DataFrame()
    )
    if not g_bathy.empty:
      g_bathy_trunc = g_bathy[g_bathy["Distance"] <= shortest_bathy_limit]
      ax_right.plot(
          g_bathy_trunc["Distance"] / 1000,
          g_bathy_trunc["Depth"],
          color=base_color,
          alpha=0.6,
          linewidth=0.8,
          zorder=2,
      )

  # CALCULATE AND PLOT GROUP MEANS (TOPOGRAPHY EXCLUDES DUPES)
  if max_topo_seen > 0:
    topo_grid = np.arange(0, max_topo_seen + grid_spacing, grid_spacing)
    for gid in topo_glaciers_in_cluster:
      g_topo = c_topo[c_topo["real_id"] == gid].sort_values("dist")
      if len(g_topo) > 1:
        interp_func = interp1d(
            g_topo["dist"],
            g_topo["elev"],
            bounds_error=False,
            fill_value="extrapolate",
        )
        topo_means_list.append(interp_func(topo_grid))
    if topo_means_list:
      mean_topo = np.nanmean(topo_means_list, axis=0)
      ax_left.plot(
          -topo_grid / 1000,
          mean_topo,
          color=base_color,
          linewidth=2.5,
          linestyle="-",
          alpha=1.0,
          zorder=4,
      )

  if shortest_bathy_limit > 0:
    bathy_grid = np.arange(0, shortest_bathy_limit + grid_spacing, grid_spacing)
    for gid in all_glaciers_in_cluster:
      g_bathy = (
          c_bathy[c_bathy["real_id"] == gid].sort_values("Distance")
          if not c_bathy.empty
          else pd.DataFrame()
      )
      if len(g_bathy) > 1:
        interp_func = interp1d(
            g_bathy["Distance"],
            g_bathy["Depth"],
            bounds_error=False,
            fill_value="extrapolate",
        )
        bathy_means_list.append(interp_func(bathy_grid))
    if bathy_means_list:
      mean_bathy = np.nanmean(bathy_means_list, axis=0)
      ax_right.plot(
          bathy_grid / 1000,
          mean_bathy,
          color=base_color,
          linewidth=2.5,
          linestyle="-",
          alpha=1.0,
          zorder=4,
      )

  # SET LIMITS & ALIGNMENT
  ax_left.set_xlim(-max_topo_limit / 1000, 0)
  ax_right.set_xlim(0, shortest_bathy_limit / 1000)

  # Uniform shared Y limits calculation
  all_y_min, all_y_max = -500, 500
  y_elements = []
  if not c_topo.empty:
    y_elements.extend([c_topo["elev"].min(), c_topo["elev"].max()])
  if not c_bathy.empty:
    c_bathy_trunc = c_bathy[c_bathy["Distance"] <= shortest_bathy_limit]
    if not c_bathy_trunc.empty:
      y_elements.extend(
          [c_bathy_trunc["Depth"].min(), c_bathy_trunc["Depth"].max()]
      )

  if y_elements:
    all_y_min, all_y_max = min(y_elements), max(y_elements)
    y_buf = (all_y_max - all_y_min) * 0.1
    all_y_min -= y_buf
    all_y_max += y_buf

  ax_left.set_ylim(all_y_min, all_y_max)
  ax_right.set_ylim(all_y_min, all_y_max)

  # REMOVE DECIMAL POINTS FROM BOTH X-AXES
  left_ticks = ax_left.get_xticks()
  ax_left.set_xticks(left_ticks)
  ax_left.set_xticklabels([f"{int(abs(tick))}" for tick in left_ticks])

  right_ticks = ax_right.get_xticks()
  ax_right.set_xticks(right_ticks)
  ax_right.set_xticklabels([f"{int(abs(tick))}" for tick in right_ticks])

  # DESIGN, LABELS, AND TITLES
  ax_left.set_ylabel("Elevation [m]", fontsize=10, fontweight="bold")
  ax_left.text(
      0.03,
      0.82,
      f"Group {int(cluster)}",
      transform=ax_left.transAxes,
      fontsize=11,
      fontweight="bold",
  )

  ax_left.grid(True, linestyle=":", alpha=0.3)
  ax_right.grid(True, linestyle=":", alpha=0.3)
  ax_right.yaxis.set_tick_params(labelleft=False)

  # ADD COLUMN HEADERS (ONLY ON THE TOP ROW SUBPLOTS)
  if i == 0:
    ax_left.set_title("BedMachine v6", fontsize=9, fontweight="bold", pad=12)
    ax_right.set_title(
        "International Bathymetric Chart of the Arctic Ocean (IBCAO)",
        fontsize=9,
        fontweight="bold",
        pad=12,
    )

  # Handle Bottom Row X-labels vs Middle Row Blanking
  if i == n_clusters - 1:
    ax_left.set_xlabel(
        "◄ Upstream Distance (km)", fontsize=10, fontweight="bold", loc="right"
    )
    ax_right.set_xlabel(
        "Downstream Distance (km) ►", fontsize=10, fontweight="bold", loc="left"
    )
  else:
    ax_left.tick_params(axis="x", labelbottom=False)
    ax_right.tick_params(axis="x", labelbottom=False)

# Save final render
output_filename = os.path.join(
    output_dir, "Shortest_Restricted_Mean_Profiles.png"
)
plt.savefig(output_filename, dpi=300, bbox_inches="tight")
plt.show()
