import numpy as np
import matplotlib.pyplot as plt
import time

from data_processing import RegionProcessor, SumCalculator, ConvCalculator, BalanceCalculator
from data_loading import  DataLoader
from containers import Region


REGION = Region(
    up = 65,
    down = 55,
    left = 130,
    right = 140,
)

START_DAY = 39
END_DAY = 69


def main():
    # data_path = "../PWV_flow_._2012_01_.nc"
    # target_name = "PWV"
    data_path = "../CO_flow_2022.nc"
    target_name = "20220601_mean"
    data_loader = DataLoader(data_path, target_name)
    # data_loader.setRegionId(processor.id)

    # обрабатываем регион
    grid = data_loader.getGrid()
    processor = RegionProcessor(REGION, grid)
    regdata = processor.getRegionData()

    balance_calc = BalanceCalculator(regdata, data_loader, (START_DAY, END_DAY))
    balance = balance_calc.calcBalanceSeries()

    x = np.arange(balance.size)
    plt.plot(x, balance)
    plt.savefig("balance_2.png")

    data_loader.close()


if __name__ == "__main__":

    start_time = time.time()
    main()
    end_time = time.time()

    print(f"time: {round(end_time - start_time, 2)} s")
