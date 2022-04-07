# Geodata Processing

## Tiled Datasets

### `checkurls.py`

Check URLs in geojson of indexed datasets to confirm they resolve.

#### Usage

```bash
checkurls.py [-h] [-v] [--version] searchPath

positional arguments:
  searchPath     Path to geojson or geojsons.

optional arguments:
  -h, --help     show this help message and exit
  -v, --verbose  Write successful responses to log as well.
  --version      show program's version number and exit
```

#### Example

```bash
# Write only bad requests to log
python checkurls.py "test datasets/"

# Write all responses to log
python checkurls.py "test datasets/adams-2010-BareEarthPointsLAS.geojson" -v
```