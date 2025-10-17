#!python
from pathlib import Path
import pickle

hash_dict = {}

# Load it back
with open("geo_translate_English_Chinese_hash.pickle.bin", "rb") as f:
    hash_dict = pickle.load(f)

print(f"Total {len(hash_dict)} items in the hash_dict")