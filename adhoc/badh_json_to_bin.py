from arduboy.bloggingadeadhorse import *
import gui_common
import json

# First, gotta get that json
print("Downloading cart meta...")
cartmeta = gui_common.get_official_cartmeta(force = True)
print(f"Cartmeta total: {len(cartmeta)}")

with open("badh_last.json", "w") as f:
    json.dump(cartmeta, f, cls=CartMetaDecoder)

# Then, gotta compute the update against an empty nothing
print("Computing update...")
update = compute_update([], cartmeta)
print(f"Updates: {len(update[UPKEY_UPDATES])} | New: {len(update[UPKEY_NEW])} | Current: {len(update[UPKEY_CURRENT])} | Unmatched: {len(update[UPKEY_UNMATCHED])}")

# Now, just pull all the little bits out of the update and the new fields and make a csv
print("Creating csv...")
csv = create_csv(update[UPKEY_NEW] + [f[1] for f in update[UPKEY_UPDATES]])

with open("badh_csvsubmit.csv", "w") as f:
    f.write(csv)
