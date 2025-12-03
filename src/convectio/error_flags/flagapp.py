### This module follows the error flag convention provided for QC'd CoMeT data. README and all QC as of Sep. 2025 has been provided and performed by
### Dr. Adam Houston at UNL.
### Created 23 September 2025 by Kyle Brooks.

### Blank now, but intended to separate off error handling from flags into separate module so raw data will be relatively unaffected if the user wishes.

import pandas as pd
from convectio import Transect


def apply_qc(df: pd.DataFrame = None):
    """Apply QC flags based on user defined conditions"""
    d_count = 0
    for index, row in df.iterrows():
        string = df["error_flag"][index]
        split = string.split("-")
        if split[2] == "tf02":
            df = df.drop(index, axis=0)
            d_count = d_count + 1

        elif split[3] == "ts02":
            df = df.drop(index, axis=0)
            d_count = d_count + 1

        elif split[6] == "w08":
            df = df.drop(index, axis=0)

        d_count = d_count + 1

    print("QC filter complete. Dropped {} rows.".format(d_count))

    return df  # gotta return this >:(
