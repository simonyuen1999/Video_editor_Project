#!python
from pathlib import Path
import pickle

# The translation mapping dictionary should be accessible everywhere in this module.
hash_dict: dict[str, str] = {}

def load_translation_mappings(input_file: str = "geo_chinese_.list") -> None:
    """Populate the global ``hash_dict`` from the provided CSV file."""
    global hash_dict
    hash_dict.clear()

    file_path = Path(input_file)
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    with file_path.open("r", encoding="utf-8") as f:
        # Skip header line if present
        next(f, None)

        # The data columns are expected to be:
        # City_en,City_zn,Region_en,Region_zn,Subregion_en,Subregion_zn,
        # CountryCode,Country_en,Country_zn,TimeZone,Latitude,Longitude
        for raw_line in f:
            data_line = raw_line.strip()
            if not data_line:
                continue

            parts = data_line.split(",")
            if len(parts) < 12:
                continue

            city_en, city_zn = parts[0], parts[1]
            region_en, region_zn = parts[2], parts[3]
            subregion_en, subregion_zn = parts[4], parts[5]
            country_en, country_zn = parts[7], parts[8]

            def add_mapping_if_needed(english: str, translated: str) -> None:
                if (
                    english
                    and translated
                    and english != "Unknown"
                    and translated != "Unknown"
                    and english.lower() != translated.lower()
                    and english not in hash_dict
                ):
                    hash_dict[english] = translated

            add_mapping_if_needed(city_en, city_zn)
            add_mapping_if_needed(region_en, region_zn)
            add_mapping_if_needed(subregion_en, subregion_zn)
            add_mapping_if_needed(country_en, country_zn)

def save_hash_to_file(output_file: str = "geo_translate_English_Chinese_hash.pickle.bin") -> None:
    global hash_dict
    with open(output_file, "wb") as f:
        pickle.dump(hash_dict, f)

def main(input_file: str = "geo_edit.list") -> None:
    global hash_dict
    load_translation_mappings(input_file)
    save_hash_to_file()
    print(f"Total {len(hash_dict)} items in the hash_dict")
    print(f"Hash saved to geo_translate_English_Chinese_hash.pickle.bin")

if __name__ == "__main__":
        main()
