Two scripts made for getting distances between zipcodes.

I arbitrary split them and used files as an interface to try to make them more composable,
but there's nothing stopping you from moving one's code into the other file to execute them in one shot.

The first script, `zips_to_latlong.py` contains a list of zipcodes that should be updated.
When run, it will geocode all these zip codes into latitude & longitude pairs using OpenStreetMaps.
Then, it will write a CSV file which contains zipcode, latitude, and longitude as its three columns per row.

The second script, `zll_to_distances.py` contains an origin zipcode variable, and a list of zipcodes to calculate the distances to.
For each zip code in the list, it will calculate the distance between the origin's lat / long, and the destination zip's lat long.
Finally, it will write these distances out to a .txt file of your choice.
You can control whether the output is verbose: `The distance between <ORIGIN> and <DESTINATION> is <DISTANCE>mi`
Or sparse: `<DISTANCE>`
Within the script's global configuration

### Quickstart
Open the scripts and update the global configuration for your usecase.
Then, run.
With poetry:
```bash
# Install dependency
poetry install

# Start the venv
poetry shell

# Run the first script, which will generate a CSV of zipcodes to their lat/long coords.
poetry run python3 zips_to_latlong.py

# Run the second script, which will generate a TXT of distances between origin and each desination zipcode.
poetry run python3 zll_to_distances.py
```

With vanilla python:
```bash
pip3 install geopy
python3 zips_to_latlong.py
python3 zll_to_distances.py
```

