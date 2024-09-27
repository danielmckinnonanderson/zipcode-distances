from math import trunc
from typing import Dict, List, Tuple
from geopy import distance

# TODO - Update configuration globals for your usecase
input_file_path: str = "./zips_lat_long.csv"
output_file_path: str = "distances.txt"

origin_zip = "00000"

destination_zips: List[int | str] = [
    # TODO - Put zipcodes here. Quote ones that begin with a 0.
]

# Switch to false to output only the distances, with no other text on the line
verbose_output: bool = True

def load_zll_from_csv(input_file_path: str) -> Dict[str, Tuple[str, str]]:
    result = {}

    with open(input_file_path, "r") as zll_csv:
        lines = zll_csv.readlines()
        for i in range(len(lines)):
            line = lines[i]
            cols = line.split(",")
            assert len(cols) == 3, f"Expected {input_file_path} to have 3 columns per row"

            # Remove trailing newline character from final column
            cols[2] = cols[2].rstrip()
            
            if i == 0:
                # Header row, assert that structure follows expectations
                assert cols[0] == "zipcode", f"Expected first column in {input_file_path} to be 'zipcode', instead was '{cols[0]}'"
                assert cols[1] == "lat", f"Expected first column in {input_file_path} to be 'lat', instead was '{cols[1]}'"
                assert cols[2] == "lon", f"Expected column column in {input_file_path} to be 'lon', instead was '{cols[2]}'"
                # After verification, skip header row
                continue

            zipcode = cols[0]
            lat     = cols[1]
            lon     = cols[2]

            result[zipcode] = (lat, lon)
    return result 


# Return the float distance between the two zipcodes
# Return None if either of the zips could not be found in the table
def compute_one_distance(
    origin_zip: str,
    destination_zip: str,
    lookup_table: Dict[str, Tuple[str, str]]
) -> float | None:
    assert len(origin_zip) == 5, "Origin zipcode was not 5 characters long"
    assert len(destination_zip) == 5, "Destination zipcode was not 5 characters long"

    try:
        orig_coords = lookup_table[origin_zip]
        dest_coords = lookup_table[destination_zip]

        if orig_coords is None:
            print(f"Can't compute distance because '{origin_zip}' was not present in the lookup table")
            return None
        if dest_coords is None:
            print(f"Can't compute distance because '{destination_zip}' was not present in the lookup table")
            return None

        dist = distance.distance((orig_coords[0], orig_coords[1]), (dest_coords[0], dest_coords[1]))
        return dist.miles
    except KeyError:
        print(f"Can't compute distance because '{origin_zip}' or '{destination_zip}' were not present in the lookup table")
        pass
    return None


# Return a dictionary with 'destination_zip' keys, and distance from origin (as miles) values
def compute_distances(
        origin: str,
        destinations: List[str | int],
        lookup_table: Dict[str, Tuple[str, str]],
        truncate_floats: bool = False
) -> Dict[str, float]:

    distances = {}

    # Track table keys visited, to warn the user if any were
    #  never used (because why would they be in the lookup table then?)
    nvr_visited = list(lookup_table.keys())

    nvr_visited.remove(origin)
    
    for dest in destinations:
        result: float | None = compute_one_distance(origin, str(dest), lookup_table)
        if result == None:
            # Couldn't get this distance, move on
            print(f"Couldn't get distance for '{origin}' '{str(dest)}'")
            continue
        
        if truncate_floats:
            distances[dest] = trunc(result)
        else:
            distances[dest] = result

        if str(dest) in nvr_visited:
            nvr_visited.remove(str(dest))

    nvr_visited_len = len(nvr_visited)
    if nvr_visited_len != 0:
        print(f"Warning -- Expected to have used every item in the zipcode lat/long table, but {nvr_visited_len} entries were never used.")
        for unvisited in nvr_visited:
            print(f"Warning -- Never used zipcode '{unvisited}'")

    return distances


def write_to_txt_file(
        origin,
        distances: Dict[str, float],
        output_file_path: str,
        verbose_output: bool = True):
    with open(output_file_path, 'w') as output:
        if verbose_output:
            for dest, dist in distances.items():
                output.write(f"Distance from {origin} to {dest}: {dist}mi\n")
        else:
            for dest, dist in distances.items():
                # Assumes the user knows that the output order is same as input.
                output.write(str(dist) + "\n")


if __name__ == "__main__":
    zll_lookup_table = load_zll_from_csv(input_file_path)
    print(f"Lookup table has length {len(zll_lookup_table)}")

    distances: Dict[str, float] = compute_distances(str(origin_zip),
                                                    destination_zips,
                                                    zll_lookup_table,
                                                    truncate_floats=True)

    write_to_txt_file(origin_zip,
                      distances,
                      output_file_path,
                      verbose_output)

    print(f"Done! Check output file at '{output_file_path}'")

