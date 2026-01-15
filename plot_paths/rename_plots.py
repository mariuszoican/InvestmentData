import os
import shutil

import pandas as pd

metadata = pd.read_csv("../simulations/round_metadata.csv")
dst_dir = "renamed_plots"

for r in range(1, 15):
    seed = int(metadata[metadata["round_number"] == r]["seed"].mean())
    info = int(metadata[metadata["round_number"] == r]["informative"].mean())
    print(seed, info)

    for access in ["access", "noaccess"]:
        old_name = f"sim_seed-{seed}_info-{info}_{access}.png"
        new_name = f"round_{r:02d}_{access}_seed_{seed}.png"

        src_file = os.path.join(f"sim_seed-{seed}_info-{info}_{access}.png")
        dst_file = os.path.join(dst_dir, f"round_{r:02d}_{access}_seed_{seed}.png")

        if os.path.exists(src_file):
            shutil.copy2(src_file, dst_file)
            print(f"Copied → {dst_file}")
        else:
            print(f"Missing: {src_file}")
