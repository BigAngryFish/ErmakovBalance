import numpy as np
import time

from data_processing import RegionProcessor, SumCalculator, ConvCalculator
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
    data_loader = DataLoader(data_path, target_name)
    # data_loader.setRegionId(processor.id)

    # обрабатываем регион
    processor = RegionProcessor(REGION)
    regdata = processor.getRegionData()

    
    # расчет суммы (для первой карты)
    sum_calculator = SumCalculator(regdata)
    firstmap = data_loader.getTargetMap(0)
    pwv_sum = sum_calculator(firstmap)

    # расчет конвергенции (для каждой единицы времени)
    conv_calculator = ConvCalculator(regdata)
    pwv_conv = 0
    for day_id in range(data_loader.timedim):
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
