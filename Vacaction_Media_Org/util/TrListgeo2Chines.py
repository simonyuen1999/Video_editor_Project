#!python

from googletrans import Translator

def translate_location_fields(file_path='geo.list'):
    translator = Translator()
    geo_data = []
    idx = 1
    with open(file_path, 'r', encoding='utf-8') as f:
        next(f)
        for line in f:
            # Each line is comma-separated values and values are 0:City,1:Region,2:Subregion,3:CountryCode,4:Country,5:TimeZone,6:FeatureCode,7:Population,8:Latitude,9:Longitude
            # After splitting, we want to store (Latitude, Longitude, City, Region, Subregion, CountryCode, Country)
            parts = line.strip().split(',')
            try:
                lat = float(parts[8])
                lon = float(parts[9])
                
                # Handle empty or null fields before translation
                city_en = parts[0].strip() if parts[0].strip() else "Unknown"
                region_en = parts[1].strip() if parts[1].strip() else "Unknown"
                subregion_en = parts[2].strip() if parts[2].strip() else "Unknown"
                country_en = parts[4].strip() if parts[4].strip() else "Unknown"
                
                # Translate with error handling
                try:
                    city_result = translator.translate(city_en, src='en', dest='zh-cn')
                    city = city_result.text if city_result and city_result.text else city_en
                except Exception as e:
                    print(f"Translation error for city '{city_en}': {e}")
                    city = city_en
                
                try:
                    region_result = translator.translate(region_en, src='en', dest='zh-cn')
                    region = region_result.text if region_result and region_result.text else region_en
                except Exception as e:
                    print(f"Translation error for region '{region_en}': {e}")
                    region = region_en
                
                try:
                    subregion_result = translator.translate(subregion_en, src='en', dest='zh-cn')
                    subregion = subregion_result.text if subregion_result and subregion_result.text else subregion_en
                except Exception as e:
                    print(f"Translation error for subregion '{subregion_en}': {e}")
                    subregion = subregion_en
                
                country_code = parts[3]
                
                try:
                    country_result = translator.translate(country_en, src='en', dest='zh-cn')
                    country = country_result.text if country_result and country_result.text else country_en
                except Exception as e:
                    print(f"Translation error for country '{country_en}': {e}")
                    country = country_en
                
                geo_data.append((lat, lon, city, region, subregion, country_code, country))

                print(f"idx {idx}: City: {city}, Region: {region}, Subregion: {subregion}, Country: {country}")
                idx += 1

            except (ValueError, IndexError) as e:
                print(f"Error parsing line in geo.list: {line.strip()}, Error: {e}")
                continue

    return geo_data

# Example usage
geo_file = "geo.list"
results = translate_location_fields(geo_file)

# Write the translated results to a new file
with open("geo_chinese.list", "w", encoding="utf-8") as outf:
    outf.write("City,Region,Subregion,CountryCode,Country,Latitude,Longitude\n")
    for entry in results:
        outf.write(f"{entry[2]},{entry[3]},{entry[4]},{entry[5]},{entry[6]},{entry[0]},{entry[1]}\n")
