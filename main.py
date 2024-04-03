import numpy as np
import time

from data_processing import RegionProcessor, DataLoader
from containers import Region


REGION = Region(
    up = 55,
    down = 45,
    left = 128,
    right = 135,
)


def main():
    data_path = "../PWV_flow_._2012_01_.nc"
    target_name = "PWV"

    data_loader = DataLoader(data_path, target_name)
    data = data_loader.data

    processor = RegionProcessor(REGION)
    pwv_sum = processor.calcSum(data.target)

    print("sum: {:e}".format(pwv_sum))


if __name__ == "__main__":

    start_time = time.time()
    main()
    end_time = time.time()

    print(f"time: {round(end_time - start_time, 2)} s")
