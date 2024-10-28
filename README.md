Script for calculating distances between zipcodes.
Start with a CSV file of your input data, containing columns `origin` and `destination` which are zip codes.
End with an output CSV file with columns `origin_zip`, `destination_zip`, and `distance` in miles.

### Quickstart
Create a file "zipcodes.csv" in this directory.
Include all zip codes that you need to calculate distances to, in order, including duplicates if that is how you want the output to look.

The input file's content should look something like this:
```csv
origin,destination
90210,02120
33101,12345
11201,64582
```
Put this content in a file "zipcodes.csv" in the directory you'll run the script in.

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
Be sure to update the file names for both your input and output.


Then, run.
Vanilla python:
```bash
python3 zipcode_distances/__init__.py
```

With poetry:
```bash
poetry run python3 zipcode_distances/__init__.py
```

