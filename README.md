Script for calculating distances between zipcodes.
Start with a text file of zip codes and an origin zip code,
end with a CSV file with columns `origin_zip`, `destination_zip`, `distance` in miles.

### Quickstart
Create a file "zipcodes.txt" in this directory.
Include all zip codes that you need to calculate distances to, in order, including duplicates if that is how you want the output to look.
Origin zip code should be first row of the file.

The file's content should look something like this:
```txt
90210
33101
11201
00123
```

Then, install dependencies:
```bash
pip3 install geopy
pip3 install colorama
```

Or, install dependencies with poetry:
```bash
poetry shell
poetry install
```


Open the script file in `./zipcode_distances/__init__.py`, and update the configuration variables at the top for your use.
Be sure to update the `origin_zipcode` -- The other defaults are likely fine for most users but your use will probably require a unique origin.


Then, run.
Vanilla python:
```bash
python3 zipcode_distances/__init__.py
```

With poetry:
```bash
poetry run python3 zipcode_distances/__init__.py
```

