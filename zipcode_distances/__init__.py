from functools import reduce
import time
import random
from typing import Dict, List, Tuple
from geopy import distance
from geopy.exc import GeocoderRateLimited, GeocoderTimedOut
from geopy.geocoders import Nominatim
from pathlib import Path
from geopy.geocoders.arcgis import Location
from colorama import Fore, init as colorama_init

# List of zipcodes to geocode
zipcodes_file: Path  = Path("./zipcodes.csv")

# Where we'll write our cached geocoded zips (to prevent rate-limit)
geocode_cache_file: Path = Path("./geocode_cache.csv")

# Where we'll write our final output, the csv of origin zip, destination zip, and distance in miles
distances_file: Path = Path("./distances.csv")


# Initialize colorful output messages
colorama_init()
def warn(message: str):
    print(Fore.YELLOW + f"WARN: {message}" + Fore.RESET)

def printerr(message: str):
    print(Fore.RED + f"ERROR: {message}" + Fore.RESET)

def info(message: str):
    print(f"INFO: {message}")


def request_geocode(zipcode: str, _geocoder: Nominatim) -> Location | None:
    try:
        query = {
            "postalcode": zipcode,
            "country": "US"
        }

        if len(zipcode) > 5:
            warn(f"Postal code '{zipcode}' appears to be Canadian. Adding country code 'CA' to query.")
            query["postalcode"] = zipcode
            query["country"] = "CA"

        result: Location = _geocoder.geocode(query=query)
        return result

    except GeocoderTimedOut:
        info(f"Geocoder timed out on '{zipcode}'. Retrying...")
        time.sleep(random.randint(100, 2 * 97) / 100)
        return request_geocode(zipcode, _geocoder)

    except GeocoderRateLimited:
        info(f"Geocoder hit a rate limit on '{zipcode}'. Retrying after wait...")
        time.sleep(random.randint(100, 2 * 141) / 100)
        return request_geocode(zipcode, _geocoder)

    except Exception as e:
        printerr(f"Geocoding encountered exception {e}")

    return None


def load_zipcodes_from_file(filepath: Path) -> List[Tuple[str, str]] | None:
    if not str(filepath).endswith(".csv"):
        printerr(f"Zipcodes file '{filepath}' is not a .csv file. Make sure the extension is correct and retry.")
        return None

    try:
        result: List[Tuple[str, str]] = []

        with open(filepath, "r") as zipcodes_file:
            lines = zipcodes_file.readlines()

            header = lines.pop(0)
            cols = header.split(",")
            if len(cols) != 2:
                printerr("Expected zipcodes file to have two columns (origin and destination). Is your input file formatted correctly?")
                return None

            for line in lines:
                line = line.rstrip()
                if line.isspace() or line == "":
                    continue

                cols = line.split(",")

                result.append((cols[0], cols[1]))

        info("Found {len(result)} rows in zipcodes.csv")
        return result
    
    except FileNotFoundError:
        printerr(f"Zipcodes file does not exist. Check if the filepath '{filepath}' you provided exists.")


def load_cached_geocoded_zipcodes(filepath: Path) -> Dict[str, Tuple[float, float]] | None:
    if not str(filepath).endswith(".csv"):
        printerr(f"Geocode cache file '{filepath}' is not a .csv file. Make sure the extension is correct and retry.")
        return None

    try:
        result = {}

        with open(filepath, "r") as cache_file:
            lines = cache_file.readlines()

            if len(lines) == 0:
                warn("Cache file was empty")
                return None
            
            header = lines.pop(0)
            parts = header.split(",")
            if len(parts) != 3:
                printerr(f"Expected cache file '{filepath}' to have three columns. Instead, the header indicates that it has '{len(parts)}'.")
            if parts[0] != "zipcode":
                printerr(f"Expected the first header section of CSV '{filepath}' to be 'zipcode', instead was '{parts[0]}'. Either correct the header or completely delete the file and re-generate it.")
            if parts[1] != "latitude":
                printerr(f"Expected the first header section of CSV '{filepath}' to be 'latitude', instead was '{parts[0]}'. Either correct the header or completely delete the file and re-generate it.")
            if parts[2].rstrip() != "longitude":
                printerr(f"Expected the first header section of CSV '{filepath}' to be 'longitude', instead was '{parts[0]}'. Either correct the header or completely delete the file and re-generate it.")

            info(f"Geocode cache file has {len(lines)} rows. Loading...")

            for line in lines:
                line = line.rstrip()
                parts = line.split(",")

                zipcode   = parts[0]
                latitude  = parts[1]
                longitude = parts[2]

                result[zipcode] = (latitude, longitude)

        info(f"Done loading cache file into memory. Cache has {len(lines)} entries.")
        return result

    except FileNotFoundError:
        info(f"Geocode cache file '{filepath}' does not exist.")

    return None



def request_and_cache_all(zipcodes: List[Tuple[str, str]], cache: Dict[str, Tuple[float, float]]):
    # Use to calculate a random time to wait, to seem more "organic" when requesting
    # These times are in milliseconds
    get_time_to_wait = lambda: random.randint(278, 3221)

    # The input zipcodes is expected to reflect the structure of the CSV file, with two zips per row.
    # So first, we'll convert this list into a flattened list structure.
    zips_list: List[str] = reduce(lambda acc, pair: acc + list(pair), zipcodes, [])
    info(f"{len(zips_list)}")

    qt_done     = int(len(zips_list) * 0.25)
    hf_done     = int(len(zips_list) * 0.50)
    tq_done     = int(len(zips_list) * 0.75)
    almost_done = int(len(zips_list) * 0.90)
    last_update = 0

    number_cached = 0
    number_requested = 0
    time_to_wait = 0.0

    n = 0
    
    for zipcode in zips_list:
        n += 1
        # Progress update
        if n >= qt_done and n < hf_done and last_update != qt_done:
            info(f"25% done processing zipcodes for cache. Progress {n}/{len(zips_list)}")
            last_update = qt_done
        elif n >= hf_done and n < tq_done and last_update != hf_done:
            info(f"50% done processing zipcodes for cache. Progress {n}/{len(zips_list)}")
            last_update = hf_done
        elif n >= tq_done and n < almost_done and last_update != tq_done:
            info(f"75% done processing zipcodes for cache. Progress {n}/{len(zips_list)}")
            last_update = tq_done
        elif n >= almost_done and last_update != almost_done:
            info(f"90% done processing zipcodes for cache. Progress {n}/{len(zips_list)}")
            last_update = almost_done


        # Check if it's already cached
        if zipcode in cache:
            number_cached += 1
            continue

        user_agent = "ethical_{}".format(random.randint(1000, 999999))
        geocoder = Nominatim(user_agent=user_agent)

        try:
            location: Location | None = request_geocode(zipcode, geocoder)

            if location is None:
                warn(f"Zipcode '{zipcode}' was unable to be geocoded and will be skipped.")
                continue
            
            cache[zipcode] = (location.latitude, location.longitude)
            number_requested += 1
            
            time_to_wait = get_time_to_wait()
            time.sleep(time_to_wait * 0.001)

        except:
            warn(f"Zipcode '{zipcode}' was unable to be geocoded and will be skipped.")
            pass

    info(f"100% Done requesting geocodes for {len(zips_list)} zipcodes. {number_cached} were already cached and did not need to be requested. Made {number_requested} requests to fill in the rest.")
    if number_requested + number_cached != len(zips_list) != len(cache):
        warn(f"You provided {len(zipcodes)} rows containing a total of {len(zips_list)} zipcodes, but only {number_cached + number_requested} were accounted for between the cache and the requests. "
             + "Check earlier log output to see which ones were skipped, if any.")


def write_cache_to_csv(csv_filepath: Path, cache: Dict[str, Tuple[float, float]]):
    if not csv_filepath.exists():
        csv_filepath.touch()

    with open(csv_filepath, "w") as cache_file:
        cache_file.write("zipcode,latitude,longitude\n")

        for key, value in cache.items():
            cache_file.write(f"{key},{value[0]},{value[1]}\n")

    info(f"Wrote cache to '{csv_filepath}'.")


def compute_distance(origin_zipcode: str, destination_zipcode: str, cache: Dict[str, Tuple[float, float]]) -> float | None:
    try:
        if origin_zipcode == destination_zipcode:
            warn(f"Was asked to compute the distance between {origin_zipcode} and {destination_zipcode}, this was probably a mistake. Skipping.")
            return None

        if origin_zipcode not in cache:
            printerr(f"Couldn't find zipcode '{origin_zipcode}' in cache. Skipping calculation...")
            return None

        if destination_zipcode not in cache:
            printerr(f"Couldn't find zipcode '{destination_zipcode}' in cache. Skipping calculation...")
            return None

        origin = cache[origin_zipcode]
        destination = cache[destination_zipcode]
        return distance.distance(origin, destination).miles
    except KeyError | ValueError:
        printerr(f"Couldn't compute distance between '{origin_zipcode}' and '{destination_zipcode}'")
    return None


def compute_distances(rows: List[Tuple[str, str]], cache: Dict[str, Tuple[float, float]]) -> Dict[Tuple[str, str], float]:
    info(f"Computing distances for {len(rows)} rows...")

    result = {}

    for pair in rows:
        if pair[0] not in cache:
            warn(f"Zipcode {pair[0]} was not in cache, skipping distance between {pair[0]} and {pair[1]}")
            continue
        if pair[1] not in cache:
            warn(f"Zipcode {pair[0]} was not in cache, skipping distance between {pair[0]} and {pair[1]}")
            continue

        distance = compute_distance(pair[0], pair[1], cache)
        if distance is None:
            continue
        
        result[pair] = distance

    info("Done computing distances!")
    return result


def write_distances_to_file(
        output_filepath: Path,
        input_rows: List[Tuple[str, str]],
        distances: Dict[Tuple[str, str], float]):
    if not output_filepath.exists():
        info(f"Output file for distances '{output_filepath}' does not exist. Creating...")
        output_filepath.touch()
        info("Created output file.")

    with open(output_filepath, "w") as distances_csv:
        info("Writing distances to output file...")

        # Write header row
        distances_csv.write("origin_zipcode,destination_zipcode,distance_miles\n")

        # Iterate through the input rather than the output,
        # because then we'll know if we need to write blank rows
        # for any rows that weren't able to be fetched & calculated.
        for row in input_rows:
            try:
                distance = distances[row]
                distances_csv.write(f"{row[0]},{row[1]},{distance}\n")
                continue

            except KeyError:
                # Row wasn't able to be calculated, write a blank line and continue
                pass

            distances_csv.write(",,\n")

    info(f"Done! Check '{output_filepath}' for your results.")


def main():
    zipcodes = load_zipcodes_from_file(filepath=zipcodes_file)
    if zipcodes is None:
        printerr("Zipcodes file didn't exist. Please add it and run again."
                 + " The zipcodes file should be a .csv file with a header row \"origin,destination\"")
        return
    
    cache = load_cached_geocoded_zipcodes(geocode_cache_file)
    if cache is None:
        info(f"Geocode cache is empty or not found. We will request OpenStreetMaps for {len(zipcodes)} zipcodes.")
        cache = {}

    request_and_cache_all(zipcodes, cache)
    write_cache_to_csv(geocode_cache_file, cache)

    distances = compute_distances(rows=zipcodes, cache=cache)
    write_distances_to_file(input_rows=zipcodes, output_filepath=distances_file, distances=distances)


if __name__ == "__main__":
    main()

