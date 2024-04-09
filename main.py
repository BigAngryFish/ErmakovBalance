import numpy as np
import time

from data_processing import RegionProcessor, ConvCalculator
from data_loading import  DataLoader
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

    processor = RegionProcessor(REGION)

    data_loader = DataLoader(data_path, target_name)
    # data_loader.setRegionId(processor.id)
    
    firstmap = data_loader.getTargetMap(0)
    pwv_sum = processor.calcSum(firstmap)

    conv_calculator = ConvCalculator(processor.cell)
    pwv_conv = 0
    days_amount = data_loader.timedim
    for day_id in range(days_amount):
        convdata = data_loader.getConvData(day_id, processor.id)
        pwv_conv += conv_calculator(convdata)
        # break

    print("sum: {:e}".format(pwv_sum))
    print("conv: {:e}".format(pwv_conv))

    data_loader.close()


if __name__ == "__main__":

    start_time = time.time()
    main()
    end_time = time.time()

    print(f"time: {round(end_time - start_time, 2)} s")
