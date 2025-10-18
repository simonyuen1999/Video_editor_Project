#!python

from googletrans import Translator

# Add a dictionary to cache translations
translation_cache = {}

def translate_location_fields(file_path='geo.list'):
    translator = Translator()

    # Open a new CSV file to write the translated results, and write the header line
    outf = open("geo_chinese_.list", "w", encoding="utf-8")
    outf.write("City_en,City_zn,Region_en,Region_zn,Subregion_en,Subregion_zn,CountryCode,Country_en,Country_zn,TimeZone,Latitude,Longitude\n")

    geo_data = []
    idx = 1
    with open(file_path, 'r', encoding='utf-8') as f:
        next(f)
        for line in f:
            # Input file is a comma-separated CSV file.
            # Each line contains contain 0:City,1:Region,2:Subregion,3:CountryCode,4:Country,5:TimeZone,6:FeatureCode,7:Population,8:Latitude,9:Longitude
            parts = line.strip().split(',')
            try:
                # Handle empty or null fields before translation
                city_en = parts[0].strip() if parts[0].strip() else "Unknown"
                region_en = parts[1].strip() if parts[1].strip() else "Unknown"
                subregion_en = parts[2].strip() if parts[2].strip() else "Unknown"
                country_code = parts[3]
                country_en = parts[4].strip() if parts[4].strip() else "Unknown"
                timezone = parts[5]
                feature_code = parts[6]
                population = parts[7]
                lat = float(parts[8])
                lon = float(parts[9])

                # Translate with error handling
                # If city_en is in cache, use cached value
                if city_en in translation_cache:
                    city = translation_cache[city_en]
                else:
                    try:
                        city_result = translator.translate(city_en, src='en', dest='zh-cn')
                        # Cache the translation result
                        translation_cache[city_en] = city_result.text if city_result and city_result.text else city_en
                        city = translation_cache[city_en]
                    except Exception as e:
                        print(f"Translation error for city '{city_en}': {e}")
                        city = city_en

                # if region_en is in cache, use cached value
                if region_en in translation_cache:
                    region = translation_cache[region_en]
                else:
                    try:
                        region_result = translator.translate(region_en, src='en', dest='zh-cn')
                        # Cache the translation result
                        translation_cache[region_en] = region_result.text if region_result and region_result.text else region_en
                        region = translation_cache[region_en]
                    except Exception as e:
                        print(f"Translation error for region '{region_en}': {e}")
                        region = region_en

                # if subregion_en is in cache, use cached value
                if subregion_en in translation_cache:
                    subregion = translation_cache[subregion_en]
                else:
                    try:
                        subregion_result = translator.translate(subregion_en, src='en', dest='zh-cn')
                        # Cache the translation result
                        translation_cache[subregion_en] = subregion_result.text if subregion_result and subregion_result.text else subregion_en
                        subregion = translation_cache[subregion_en]
                    except Exception as e:
                        print(f"Translation error for subregion '{subregion_en}': {e}")
                        subregion = subregion_en

                # No need to translate country_code

                # if country_result is in cache, use cached value
                if country_en in translation_cache:
                    country = translation_cache[country_en]
                else:
                    try:
                        country_result = translator.translate(country_en, src='en', dest='zh-cn')
                        # Cache the translation result
                        translation_cache[country_en] = country_result.text if country_result and country_result.text else country_en
                        country = translation_cache[country_en]
                    except Exception as e:
                        print(f"Translation error for country '{country_en}': {e}")
                        country = country_en
                
                geo_data.append((lat, lon, city, region, subregion, country_code, country))

                print(f"idx {idx}: City: {city}, Region: {region}, Subregion: {subregion}, Country: {country}")
                idx += 1

            except (ValueError, IndexError) as e:
                print(f"Error parsing line in geo.list: {line.strip()}, Error: {e}")
                continue
        
            # Write the translated results to a new file
            outf.write(f"{city_en},{city},{region_en},{region},{subregion_en},{subregion},{country_code},{country_en},{country},{timezone},{lat},{lon}\n")
            outf.flush()

    # At the end, return the whole geo_data hash (less information than the original file)
    outf.close()
    return geo_data

# Example usage
geo_file = "geo.list"
results = translate_location_fields(geo_file)
