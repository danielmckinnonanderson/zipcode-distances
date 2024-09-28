Script for calculating distances between zipcodes.
Start with a text file of zip codes and an origin zip code,
end with a CSV file with columns `origin_zip`, `destination_zip`, `distance` in miles.

### Quickstart
Create a file "zipcodes.txt" in this directory.
Include all zip codes that you need to calculate distances to, in order. Origin zip code should be first.
The file's content should look like this:
```txt
90210
33101
11201
00123
```

Next, open the script and update the global configuration variables at the top for your usecase.
You'll need to specify the path to your zipcodes file (if you followed these instructions exactly, the default "zipcodes.txt" will be correct),
along with the path to the file where you'll save your cache for the geocoded zip codes,
the path to the file where you'll save your final output, and the origin zip code itself.

Then, run.

With poetry:
```bash
# Install dependencies
poetry install

# Start the venv
poetry shell

# Run the first script, which will generate a CSV of zipcodes to their lat/long coords.
poetry run python3 zipcodes_to_distances.py
```

With vanilla python:
```bash
pip3 install geopy
pip3 install colorama # For colorful terminal output
python3 zipcodes_to_distances.py
```

