# Data sources

The large raw files are intentionally excluded from Git. This file records the
public sources and exact initial pilot scope so another researcher can obtain
the same inputs without needing a copy of the repository owner's local data.

## Initial pilot intake

| Input | Initial scope | Public source |
|---|---|---|
| Static GTFS | Version `S070_202605050858`; service dates 2026-05-10 to 2026-08-15 | [Mobility Database historical archive](https://files.mobilitydatabase.org/mdb-394/mdb-394-202605060054/mdb-394-202605060054.zip) |
| Vehicle Positions | 2026-08-10 and 2026-08-11; all Madison Metro routes retained | [gtfsrt.io archive](https://gtfsrt.io/) |
| Trip Updates | 2026-08-10 and 2026-08-11; all Madison Metro routes retained | [gtfsrt.io archive](https://gtfsrt.io/) |
| Weather | Hourly Madison weather, 2026-08-10 through 2026-08-11 | [Open-Meteo historical weather API](https://open-meteo.com/en/docs/historical-weather-api) |

The static GTFS archive must match the real-time service dates. The first
version above has SHA-1 `136519fe4b6ccf411852f42b61b5e171cdd57569`.

## Provenance policy

- Each local download is listed with a SHA-256 checksum in the ignored
  `data/manifest.csv` file.
- Raw GTFS-Realtime Parquet files are preserved unmodified.
- Vehicle Positions support GPS-derived arrival labels; Trip Updates support an
  agency-prediction baseline and are not treated as observed arrivals.
- Metro attribution: “Data provided under license granted by City of Madison,
  WI, Metro Transit.”
