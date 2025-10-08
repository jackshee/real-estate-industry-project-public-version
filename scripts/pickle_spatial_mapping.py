"""
Utility script to build the suburb combination mapping from the spatial matrix
notebook and persist it as a pickle file.
"""

from __future__ import annotations

import argparse
import pickle
from pathlib import Path
from typing import Dict, List

import geopandas as gpd
import pandas as pd


def build_mapping(panel_path: Path, locality_shp_path: Path) -> Dict[str, List[str]]:
    """Replicate the mapping logic from the notebook."""
    ts_suburbs_df = pd.read_csv(panel_path)
    suburbs_gdf = gpd.read_file(locality_shp_path)

    suburb_values = ts_suburbs_df["suburb"].astype(str).str.lower()
    locality_values = suburbs_gdf["LOCALITY"].astype(str).str.lower()

    merged_dict_list = [
        {combo: [part for part in combo.split("-") if part]}
        for combo in sorted(set(suburb_values) - set(locality_values))
    ]

    mapping = {k: v for d in merged_dict_list for k, v in d.items()}
    return mapping


def main() -> None:
    parser = argparse.ArgumentParser(description="Build and pickle the suburb mapping.")
    parser.add_argument(
        "--panel-path",
        default=Path("data/curated/rent_growth/panel_data_updates.csv"),
        type=Path,
        help="Path to the panel data CSV",
    )
    parser.add_argument(
        "--locality-shp",
        default=Path("data/geo/shpfile/LOCALITY_POLYGON.shp"),
        type=Path,
        help="Path to the locality shapefile",
    )
    parser.add_argument(
        "--output-path",
        default=Path("data/processed/mapping.pkl"),
        type=Path,
        help="Where to write the pickle file",
    )

    args = parser.parse_args()

    mapping = build_mapping(args.panel_path, args.locality_shp)
    args.output_path.parent.mkdir(parents=True, exist_ok=True)

    with args.output_path.open("wb") as f:
        pickle.dump(mapping, f)


if __name__ == "__main__":
    main()
