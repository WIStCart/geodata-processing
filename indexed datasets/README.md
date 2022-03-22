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



### `coordinate_precision.py`

Read indexed dataset GeoJSON, reduce coordinate precision, and output to specified directory.

#### Usage

```bash
coordinate_precision.py [-h] [-p PRECISION] [-v] [--version] inPath outPath

positional arguments:
  inPath                Path to geojson or geojsons.
  outPath               Output path to place updated geojsons.

optional arguments:
  -h, --help            show this help message and exit
  -p PRECISION, --precision PRECISION
                        How many digits after the decimial (default=4)
  -v, --verbose         Write successful precision changes to log as well.
  --version             show program's version number and exit
```

#### Example

```bash
# Use the default of four digits after the decimal
python coordinate_precision.py test/ test/output/

# Reduce precision to three digits and log all datasets processed
python coordinate_precision.py test/ test/output/ -p 3 -v 
```