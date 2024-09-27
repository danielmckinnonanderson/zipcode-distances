import time
from typing import Dict, List
from geopy.exc import GeocoderTimedOut
from geopy.geocoders import Nominatim
from geopy.geocoders.nominatim import Location

# TODO - Fill update global config out before running the script.

# Used to tell our geocoding provider who we are. Make this unique.
user_agent = "UPDATE ME!"

# Best practice -- This should be a relative path to the file name you want
#  to write to. This string means "write to a file called 'zips_lat_long.csv'
#  in the same directory that I'm running the script in".
output_filepath = "./zips_lat_long.csv"

# If the script fails, it will print a message indicating what index it stopped at.
# When that happens, update this value to that index to pick up where you left off.
start_at_idx = 0

# Your input data. 
zips: List[int | str] = [
    # TODO - Put zipcodes here. Quote ones that begin with a 0.
]


geocoder: Nominatim = Nominatim(user_agent=user_agent)

def get_lat_long(zipcode: str) -> Dict | None:
    result: Location = geocoder.geocode(zipcode)

    if result is not None:
         return { "lat": result.latitude, "lon": result.longitude }
    else:
         return None


def get_all_lat_longs(zipcodes: List[int | str]) -> Dict:
    print(f"Fetching lat longs for {len(zips)} zipcodes...")
    latlongs = dict()

    time_btwn_calls = 1400 # 1.4 secs
    last_time = time.time() * 1000
    last_idx = 0

    # Used to provide a progress update to user
    qtr    = len(zipcodes) * 0.25
    half   = len(zipcodes) * 0.50
    thr_qt = len(zipcodes) * 0.75
    last_prg_update = 0

    try:
        for i in range(start_at_idx, len(zipcodes)):
            zip = zipcodes[i]
            last_time = time.time() * 1000
            opt_latlong = get_lat_long(str(zip))

            if opt_latlong is None:
                print(f"Warning: Coudln't geocode zip '{zip}'")
                continue

            latlongs[zip] = opt_latlong
            last_idx = i

            # Show the user some progress update
            if last_idx > qtr and last_idx < half:
                if last_prg_update != qtr:
                    last_prg_update = qtr
                    print("25% done...")
            elif last_idx > half and last_idx < thr_qt:
                if last_prg_update != half:
                    last_prg_update = half
                    print("50% done...")
            elif last_idx > thr_qt:
                if last_prg_update != thr_qt:
                    last_prg_update = thr_qt
                    print("75% done...")

            now = time.time() * 1000
            delta = now - last_time

            to_wait = time_btwn_calls - delta
            if to_wait > 0:
                time.sleep(to_wait * 0.001)

        print(f"100% Done. Got {len(latlongs)} lat/long pairs.")
    except GeocoderTimedOut:
        print(f"Something bad happened, and I stopped at index {last_idx}\n")
        print(f"Verify that the zips in-progress are in the CSV filepath you " +
              "provided, and then update the `start_at_idx` variable with the last index " +
              "above. You should probably update the output file path to be a new file, and " +
              "merge them manually after running again.")

    return latlongs


def write_to_csv(dict: Dict, out_path: str) -> None:
    print(f"Writing to file {out_path}...")
    with open(out_path, "a") as csv:
        # Write header row
        csv.write("zipcode,lat,lon\n")

        # Push each zip, lat, long, into next line of file
        for key, value in dict.items():
            csv.write(f"{key},{value['lat']},{value['lon']}\n")
    
    print(f"Done. Check '{out_path}' for your zips & lat/long coords.")


if __name__ == "__main__":
    latlongs = get_all_lat_longs(zips)
    write_to_csv(latlongs, output_filepath)

