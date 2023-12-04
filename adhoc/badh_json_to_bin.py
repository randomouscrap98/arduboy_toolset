import sys
import os

# All because vscode debugger or whatever
thisdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(thisdir)
os.chdir(thisdir)
sys.path.append(parentdir)  # Add the parent directory to the Python path

import arduboy.arduhex
from arduboy.bloggingadeadhorse import *
from gui_common import *
import json

# First, gotta get that json
print("Downloading cart meta...")
cartmeta = get_official_cartmeta(force = True)
print(f"Cartmeta total: {len(cartmeta)}")

with open("badh_last.json", "w") as f:
    json.dump(cartmeta, f, cls=CartMetaDecoder)

# Then, gotta compute the update against an empty nothing
print("Computing update...")
update = compute_update([], cartmeta, arduboy.arduhex.DEVICE_ARDUBOYFX)
print(f"Updates: {len(update[UPKEY_UPDATES])} | New: {len(update[UPKEY_NEW])} | Current: {len(update[UPKEY_CURRENT])} | Unmatched: {len(update[UPKEY_UNMATCHED])}")

# Now, just pull all the little bits out of the update and the new fields and make a csv
print("Creating csv...")
csv = create_csv(update[UPKEY_NEW] + [f[1] for f in update[UPKEY_UPDATES]])

with open("badh_csvsubmit.csv", "w") as f:
    f.write(csv.replace(BADH_EOL, "\n"))

# And now we post some data to the websiiiteee
print("Posting CSV, expecting bin...")
result = get_official_bin(csv)
print(f"Bin size: {len(result)}")

with open("badh_finalresult.bin", "wb") as f:
    f.write(result)

print("All done!")