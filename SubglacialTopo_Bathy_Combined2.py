import os
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd

# ============================================================
# 1. USER SETTINGS & FILE PATHS
# ============================================================
topo_file = r"C:\Users\Matia\OneDrive - Durham University\Documents\Research Masters\Data Spreadsheets\Subglacial Topography\Subglacial Topography.xlsx"
bathy_file = r"C:\Users\Matia\OneDrive - Durham University\Documents\Research Masters\Data Spreadsheets\Bathymetry\Bathymetry_Data.xlsx"
output_dir = r"C:\Users\Matia\OneDrive - Durham University\Documents\Research Masters\Figures\Combined_Profiles"

distance_bin = 500  # meters for bathymetric filtering
max_topo_limit = 5.0  # Fixed upstream km limit
max_bathy_ceil = 50.0  # Hard maximum downstream km limit

# ============================================================
# 2. DEFINITIONS & MAPPING
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

# Custom labels for combined profiles
custom_title_ids = {
    320: "320/323",
    284: "284/286",
}

os.makedirs(output_dir, exist_ok=True)

# ============================================================
# 3. LOADING DATASETS
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

glacier_bathy_map = {}
for raw_key, real_ids in id_translation.items():
    subset = df_bathy_raw[
        df_bathy_raw["Raw_ID"].astype(str).str.strip() == str(raw_key)
    ].copy()
    for rid in real_ids:
        glacier_bathy_map[rid] = subset

# ============================================================
# 4. GRID SETUP & PLOTTING (3 COLUMNS: G1 | G2+3 | G4+5+6, PORTRAIT)
# ============================================================
num_columns = 3  # Column 1: Group 1, Column 2: Groups 2 & 3, Column 3: Groups 4, 5 & 6
max_glaciers_in_col = 10  # Group 1 sets maximum vertical height to 10 rows

# A4 Portrait dimensions: 8.27 x 11.69 inches
fig = plt.figure(figsize=(8.27, 11.69))
active_plots = set()

clusters_to_plot = sorted(list(set(cluster_dict.values())))

# Group counts for offset calculations
group_2_count = len([gid for gid, c in cluster_dict.items() if c == 2])
group_4_count = len([gid for gid, c in cluster_dict.items() if c == 4])
group_5_count = len([gid for gid, c in cluster_dict.items() if c == 5])

# Target column mapping for each cluster
column_mapping = {
    1: 1,  # Column 1: Group 1
    2: 2,  # Column 2: Group 2
    3: 2,  # Column 2: Group 3
    4: 3,  # Column 3: Group 4
    5: 3,  # Column 3: Group 5
    6: 3,  # Column 3: Group 6
}

for cluster in clusters_to_plot:
    glaciers_in_cluster = sorted(
        [gid for gid, c in cluster_dict.items() if c == cluster]
    )
    cluster_color = group_colors.get(cluster, "tab:grey")

    target_col = column_mapping[cluster]

    for r_idx, gid in enumerate(glaciers_in_cluster):
        # Calculate row offset dynamically with a 1-row gap between groups
        if cluster == 3:
            visual_row = group_2_count + 1 + r_idx
        elif cluster == 5:
            visual_row = group_4_count + 1 + r_idx
        elif cluster == 6:
            visual_row = group_4_count + group_5_count + 2 + r_idx
        else:
            visual_row = r_idx

        plot_pos = (visual_row * num_columns) + target_col
        active_plots.add(plot_pos)

        ax = plt.subplot(max_glaciers_in_col, num_columns, plot_pos)
        ax.axvline(
            0, color="black", linestyle="-", linewidth=0.8, alpha=0.7, zorder=4
        )

        # A. Subglacial Topography (Left Side)
        topo_x, topo_y = np.array([]), np.array([])
        gdf_topo = df_topo_raw[
            (df_topo_raw["real_id"] == gid)
            & (df_topo_raw["dist"] <= max_topo_limit * 1000)
        ].sort_values("dist")

        if not gdf_topo.empty:
            topo_x = -gdf_topo["dist"].values / (max_topo_limit * 1000)
            topo_y = gdf_topo["elev"].values
            ax.plot(topo_x, topo_y, lw=0.9, color=cluster_color, zorder=3)

        # B. Bathymetry (Right Side)
        gdf_bathy = glacier_bathy_map.get(gid, pd.DataFrame())
        bathy_x, bathy_y = np.array([]), np.array([])
        max_bathy_dist_km = 5.0  # fallback

        if not gdf_bathy.empty:
            gdf_bathy = gdf_bathy[
                gdf_bathy["Distance"] <= max_bathy_ceil * 1000
            ].sort_values("Distance")
            if not gdf_bathy.empty:
                true_max_dist = gdf_bathy["Distance"].max()
                max_bathy_dist_km = true_max_dist / 1000

                bins = np.arange(
                    gdf_bathy["Distance"].min(),
                    true_max_dist + distance_bin + 1,
                    distance_bin,
                )
                gdf_bathy["dist_bin"] = pd.cut(
                    gdf_bathy["Distance"], bins=bins, labels=bins[:-1]
                )
                profile = (
                    gdf_bathy.groupby("dist_bin", observed=True)["Depth"]
                    .mean()
                    .reset_index()
                )
                profile["dist_bin"] = profile["dist_bin"].astype(float)

                bathy_x = profile["dist_bin"].values / true_max_dist
                bathy_y = profile["Depth"].values
                ax.plot(bathy_x, bathy_y, lw=0.9, color=cluster_color, zorder=3)

        # C. Shading Calculations
        all_y = np.concatenate([topo_y, bathy_y])
        deepest_point = all_y.min() - 50 if len(all_y) > 0 else -1000
        highest_point = max(all_y.max() + 50 if len(all_y) > 0 else 500, 100)

        if len(topo_x) > 0:
            ax.fill_between(
                topo_x,
                topo_y,
                deepest_point,
                color=cluster_color,
                alpha=0.12,
                zorder=2,
            )
        if len(bathy_x) > 0:
            ax.fill_between(
                bathy_x,
                bathy_y,
                deepest_point,
                color=cluster_color,
                alpha=0.12,
                zorder=2,
            )

        # Lock viewport boundary to [-1.0, 1.0]
        ax.set_xlim(-1.0, 1.0)
        ax.set_ylim(deepest_point, highest_point)

        # Custom Asymmetric Labels mapping back to true geographic kilometers
        tick_positions = [-1.0, -0.5, 0.0, 0.5, 1.0]
        label_values = [
            f"{int(max_topo_limit)}",
            f"{float(max_topo_limit/2):.1f}".rstrip("0").rstrip("."),
            "0",
            f"{float(max_bathy_dist_km/2):.1f}".rstrip("0").rstrip("."),
            f"{int(round(max_bathy_dist_km))}",
        ]
        ax.xaxis.set_major_locator(ticker.FixedLocator(tick_positions))
        ax.set_xticklabels(label_values)

        # Group Headers
        if r_idx == 0:
            header_y_anchor = 1.35
            ax.annotate(
                f"Group {cluster}",
                xy=(0.5, header_y_anchor),
                xycoords="axes fraction",
                fontsize=9,
                fontweight="bold",
                ha="center",
                color="black",
                annotation_clip=False,
            )

        # Subplot Header Titles - BedMachine/IBCAO only on top subplot of each column
        display_id = custom_title_ids.get(gid, str(gid))
        if visual_row == 0:
            title_text = f"◄ BedMachine v6 | {display_id} | IBCAO ►"
        else:
            title_text = f"{display_id}"

        ax.set_title(
            title_text,
            fontsize=7.5,
            fontweight="normal",
            pad=2,
        )

        # X-Labels
        is_last_in_cluster = r_idx == len(glaciers_in_cluster) - 1
        if is_last_in_cluster:
            ax.set_xlabel(
                "◄ Upstream (5km) | Downstream ►\nDistance (km)",
                fontsize=7.5,
                fontweight="bold",
            )

        ax.grid(True, linestyle="--", alpha=0.2)
        ax.tick_params(axis="both", labelsize=6.5, pad=1)

# Clean out raw unassigned cells across the 3-column setup
for total_pos in range(1, (max_glaciers_in_col * num_columns) + 1):
    if total_pos not in active_plots:
        fig.add_subplot(max_glaciers_in_col, num_columns, total_pos).axis("off")

fig.text(
    0.015,
    0.5,
    "Elevation / Depth (m)",
    fontsize=11,
    fontweight="bold",
    va="center",
    rotation="vertical",
)

# Optimized layout spacing for A4 portrait
plt.subplots_adjust(
    left=0.07, right=0.97, top=0.95, bottom=0.04, hspace=0.75, wspace=0.28
)

output_filename = os.path.join(
    output_dir, "Balanced_HalfSpace_A4_Portrait_Fixed_Ceiling.png"
)
plt.savefig(output_filename, dpi=300, bbox_inches=None)
plt.show()
