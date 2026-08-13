# Analysis code

This directory is reserved for code that analyzes data already placed in `data/`:

- GTFS schedule parsing and date matching
- GPS-derived label construction
- feature construction
- baseline and model training
- evaluation and plot generation

Do not place download, scraping, or raw-data acquisition scripts here. Those tools belong outside the project at:

```text
D:\Michael\Interesting Project\_external_data_tools\madison_bus_delay
```

The first Python source file should be added only after the static-GTFS and Vehicle-Positions data audit has established the exact Route A identifiers and input schema.

