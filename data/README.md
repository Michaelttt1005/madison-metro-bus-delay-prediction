# Local data contract

Place data you have already acquired in this folder. Large raw data files and generated tables are ignored by Git.

```text
data/
├── raw/
│   ├── gtfs/                 # Static GTFS zip files, one per schedule period
│   ├── vehicle_positions/    # Archived GTFS-RT Vehicle Positions by date
│   ├── trip_updates/         # Archived GTFS-RT Trip Updates by date
│   └── weather/              # Raw weather responses or CSV files
├── interim/                  # Parsed GTFS and joined temporary tables
└── processed/                # Labels, features, and final train/validation/test tables
```

## Required provenance

Before analysis begins, create `data/manifest.csv` with one row per acquired file or dataset. Include:

```text
source_name,source_url,local_path,date_start,date_end,
retrieved_at,static_gtfs_version,notes
```

## Important rules

- Keep the original downloaded input unchanged under `raw/`.
- Do not commit raw GTFS-RT Parquet files, API keys, or large generated tables.
- Static GTFS must match the service dates used in each analysis row.
- Keep timestamps in UTC at ingestion; convert to `America/Chicago` only for calendar and schedule features.
- Download / acquisition scripts live outside this repository at `D:\Michael\Interesting Project\_external_data_tools\madison_bus_delay`.

## Initial local sample

The acquisition tool downloads an initial two-day sample for 2026-08-10 through
2026-08-11. It uses the matching historical static GTFS archive (service window
2026-05-10 through 2026-08-15), verifies its checksum and stated service window
before it accepts the archived GTFS-Realtime files. The raw archive contains
every Metro route; Route A filtering happens later in a reproducible processing
step.
