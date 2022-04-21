# Geodata Processing

## Tiled Datasets



### `check_urls.py`

Check URLs in geojson of indexed datasets to confirm they resolve.

#### Usage

```bash
check_urls.py [-h] [-v] [--version] searchPath

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
python check_urls.py "test datasets/"

# Write all responses to log
python check_urls.py "test datasets/adams-2010-BareEarthPointsLAS.geojson" -v
```



### `coordinate_precision.py`

Read indexed dataset GeoJSON, reduce coordinate precision, and output to specified directory.

#### Usage

```bash
coordinate_precision.py [-h] [-p PRECISION]
                               [-i INDENTATION] [-s] [-v]
                               [--version]
                               inPath outPath

positional arguments:
  inPath                Path to geojson or geojsons.
  outPath               Output path to place updated geojsons.    

optional arguments:
  -h, --help            show this help message and exit
  -p PRECISION, --precision PRECISION
                        How many digits after the decimial        
                        (default=4)
  -i INDENTATION, --indent INDENTATION
                        Indent level. (default=None)
  -s, --skip-feature    Gracefully skip feature instead of        
                        entire dataset if there is an
                        unsupported geometry type.
  -v, --verbose         Write successful precision changes to     
                        log as well.
  --version             show program's version number and exit
```

#### Example

```bash
# Use the default of four digits after the decimal
python coordinate_precision.py test/ test/output/

# Reduce precision to three digits, indentation of 2, and log all datasets processed
python coordinate_precision.py test/ test/output/ -p 3 -i 2 -v
```

### `minify_geojson.py`

Minify geojson to have no return/new lines and no indentation. Optionally choose an indentation level.

#### Usage

```bash
minify_geojson.py [-h] [-i INDENTATION] path

positional arguments:
  path                  Path to geojson or geojsons.

optional arguments:
  -h, --help            show this help message and exit
  -i INDENTATION, --indent INDENTATION
                        Indent level. (default=None)
```

#### Example

```bash
# Use the default to minify
python minify_geojson.py "test/"

# Use and indentation level of four
python minify_geojson.py "test/" -i 4
```

### `update_url.py`

Update websiteUrl of geojson to specified new url.

#### Usage

```bash
update_url.py [-h] path newUrl

positional arguments:
  path        Path to geojson or geojsons.
  newUrl      The new websiteUrl.

optional arguments:
  -h, --help  show this help message and exit
```

### Example

```bash
python update_url.py "test/" "https://www.sco.wisc.edu/data/elevationlidar/"
```