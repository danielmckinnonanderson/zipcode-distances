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
zipcodes_file: Path  = Path("./zipcodes.txt")

# Where we'll write our cached geocoded zips (to prevent rate-limit)
geocode_cache_file: Path = Path("./geocode_cache.csv")

# Where we'll write our final output, the csv of origin zip, destination zip, and distance in miles
distances_file: Path = Path("./distances.csv")

# Origin zip code. Make sure this is in your zipcodes_file
origin_zipcode: str = "90210"


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


def load_zipcodes_from_file(filepath: Path) -> List[str] | None:
    if not filepath.exists():
        printerr(f"Zipcodes file does not exist. Check if the filepath '{filepath}' you provided exists.")

    result: List[str] = []

    with open(filepath, "r") as zipcodes_file:
        lines = zipcodes_file.readlines()
        for line in lines:
            if "\n" in line:
                line = line.removesuffix("\n")
            
            if "," in line:
                warn("Zipcodes file contains commas in lines, these will be ignored. Zipcodes file is expecting one zipcode per line, without quotes or delimiters.")
            
            result.append(line)

    return result

def load_cached_geocoded_zipcodes(filepath: Path) -> Dict[str, Tuple[float, float]] | None:
    if not str(filepath).endswith(".csv"):
        printerr(f"Geocode cache file '{filepath}' is not a .csv file. Make sure the extension is correct and retry.")
        return None

    filepath.touch()

    if not filepath.exists():
        info(f"Geocode cache file '{filepath}' does not exist.")
        return None

    result = {}
    
    with open(filepath, "r") as cache_file:
        lines = cache_file.readlines()

        if len(lines) == 0:
            warn("Cache file was empty")
            return None
        
        header = lines[0]
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


def request_and_cache_all(zipcodes: List[str], cache: Dict[str, Tuple[float, float]]):
    # Use to calculate a random time to wait, to seem more "organic" when requesting
    # These times are in milliseconds
    get_time_to_wait = lambda: random.randint(278, 3221)

    number_cached = 0
    number_requested = 0
    time_to_wait = 0.0

    qt_done     = int(len(zipcodes) * 0.25)
    hf_done     = int(len(zipcodes) * 0.50)
    tq_done     = int(len(zipcodes) * 0.75)
    almost_done = int(len(zipcodes) * 0.90)

    last_update = 0
    n = 0
    
    for zipcode in zipcodes:
        n += 1
        # Progress update
        if n >= qt_done and n < hf_done and last_update != qt_done:
            info(f"25% done processing zipcodes for cache. Progress {n}/{len(zipcodes)}")
            last_update = qt_done
        elif n >= hf_done and n < tq_done and last_update != hf_done:
            info(f"50% done processing zipcodes for cache. Progress {n}/{len(zipcodes)}")
            last_update = hf_done
        elif n >= tq_done and n < almost_done and last_update != tq_done:
            info(f"75% done processing zipcodes for cache. Progress {n}/{len(zipcodes)}")
            last_update = tq_done
        elif n >= almost_done and last_update != almost_done:
            info(f"90% done processing zipcodes for cache. Progress {n}/{len(zipcodes)}")
            last_update = almost_done


        # Check if it's already cached
        if zipcode in cache:
            number_cached += 1
            continue

        user_agent = "ethical_".format(random.randint(1000, 999999))
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

    info(f"100% Done requesting geocodes for {len(zipcodes)} zipcodes. {number_cached} were already cached and did not need to be requested. Made {number_requested} requests to fill in the rest.")
    if number_requested + number_cached != len(zipcodes) != len(cache):
        warn(f"You provided {len(zipcodes)} zipcodes, but only {number_cached + number_requested} were accounted for between the cache and the requests. Check earlier log output to see which ones were skipped, if any.")


def write_cache_to_csv(csv_filepath: Path, cache: Dict[str, Tuple[float, float]]):
    if not csv_filepath.exists():
        csv_filepath.touch()

    with open(csv_filepath, "w") as cache_file:
        for key, value in cache.items():
            cache_file.write(f"{key},{value[0]},{value[1]}\n")

    info(f"Wrote cache to '{csv_filepath}'.")


def compute_distance(origin_zipcode: str, destination_zipcode: str, cache: Dict[str, Tuple[float, float]]) -> float | None:
    if origin_zipcode == destination_zipcode:
        warn(f"Was asked to compute the distance between {origin_zipcode} and {destination_zipcode}, this was probably a mistake. Skipping.")
        return None

    if origin_zipcode not in cache:
        printerr(f"Couldn't find zipcode '{origin_zipcode}' in cache. Skipping calculation...")
        return None

    if destination_zipcode not in cache:
        printerr(f"Couldn't find zipcode '{destination_zipcode}' in cache. Skipping calculation...")
        return None
    
    try:
        origin = cache[origin_zipcode]
        destination = cache[destination_zipcode]
        return distance.distance(origin, destination).miles
    except KeyError | ValueError:
        printerr(f"Couldn't compute distance between '{origin_zipcode}' and '{destination_zipcode}'")
    return None


def compute_distances(origin_zipcode: str, destinations: List[str], cache: Dict[str, Tuple[float, float]]) -> Dict[Tuple[str, str], float]:
    info(f"Computing distances for {len(destinations)} elements...")

    if origin_zipcode not in cache:
        printerr(f"Origin zipcode '{origin_zipcode}' was not found in the cache. Did you forget to add it to your zipcodes file before geocoding? Please add it and run this script again, no distances can be calculated without it.")
        exit(1)

    result = {}

    for destination in destinations:
        distance = compute_distance(origin_zipcode, destination, cache)
        if distance is None:
            continue
        
        result[(origin_zipcode, destination)] = distance

    info("Done computing distances!")
    return result


def write_distances_to_file(output_filepath: Path, distances: Dict[Tuple[str, str], float]):
    if not output_filepath.exists():
        info(f"Output file for distances '{output_filepath}' does not exist. Creating...")
        output_filepath.touch()
        info(f"Created output file.")

    with open(output_filepath, "w") as distances_csv:
        info("Writing distances to output file...")

        # Write header row
        distances_csv.write("origin_zipcode,destination_zipcode,distance_miles\n")

        for key, distance in distances.items():
            (origin, destination) = key
            distances_csv.write(f"{origin},{destination},{distance}\n")

    info(f"Done! Check '{output_filepath}' for your results.")


def main():
    zipcodes = load_zipcodes_from_file(filepath=zipcodes_file)
    if zipcodes == None:
        printerr(f"Zipcodes file didn't exist. Please add it and run again. Make sure that all zipcodes you need to use in your distances are in the file, including the origin zipcode.")
        return
    
    cache = load_cached_geocoded_zipcodes(geocode_cache_file)
    if cache is None:
        info(f"Geocode cache is empty or not found. We will request OpenStreetMaps for {len(zipcodes)} zipcodes.")
        cache = {}

    request_and_cache_all(zipcodes, cache)
    write_cache_to_csv(geocode_cache_file, cache)

    distances = compute_distances(origin_zipcode=origin_zipcode, destinations=zipcodes, cache=cache)
    write_distances_to_file(output_filepath=distances_file, distances=distances)


if __name__ == "__main__":
    main()

