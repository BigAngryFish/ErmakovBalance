import numpy as np
import pandas as pd
from datetime import datetime
import time


from src.data_loading import DataLoader
from src.containers import Region
from src.reg_static import StaticMaker


# ---------- SETTINGS ----------

START_DAY = datetime(2022, 7, 22)
END_DAY = datetime(2022, 8, 22)

REGION = Region(59, 65, 59.5, 66)

DATA_PATH = "../CO_flow_2022.nc"
TARGET_VARIABLE_NAME = "20220601_mean"

# ------------------------------


def main() -> None:
    # извлекаем необходимые данные
    data = DataLoader(DATA_PATH, TARGET_VARIABLE_NAME)
    data.setDateRange(START_DAY, END_DAY)

    static_maker = StaticMaker()
    heaps = static_maker.calcHeapsOfBalances(data, REGION)

    data.close()


if __name__ == "__main__":
    start = time.time()
    main()
    end = time.time()

    print("time: {:.2f} s".format(end - start))
