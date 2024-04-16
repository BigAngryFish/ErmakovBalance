import numpy as np
import pandas as pd

from src.data_loading import DataLoader
from src.containers import Region, BalanceData, RegionBalance, HeapOfBalances
from src.data_processing import RegionProcessor, BalanceCalculator
from src.tools import Mode


class StaticMaker():
    """Класс для набора статистики по данным"""

    def __init__(self) -> None:
        """Инициализация"""

        self.bal_calc = BalanceCalculator()

    def calcHeapOfBalances(self, center_region: Region, data: DataLoader) -> HeapOfBalances:
        """
        Рассчитывает  балансы  для  регионов  с  одинаковыми параметрами высоты и ширины,
        сдвинутых относительного центрального
        """
        step_shifts = (np.arange(0, 425, 25) - 200) / 100

        balances = []
        for lat_shift in step_shifts:
            for lon_shift in step_shifts:
                working_region = center_region.addCords(lat_shift, lon_shift)
                balance = self.bal_calc.calcRegionBalance(working_region, data)
                balances.append(balance)
        
        return HeapOfBalances(balances, center_region.height, center_region.width)

    def calcHeapsOfBalances(self, data: DataLoader, region: Region):
        """
        Рассчитывает балансы для различных регионов различных размеров, сдвинутых относи-
        тельно 'region' 
        """
        size_shifts = (np.arange(0, 55, 5) - 25) / - 10

        heights = size_shifts + region.height
        widths = size_shifts + region.width

        balances = {}

        count = 0
        for height, width in zip(heights, widths):
            center_region = region.centralizeRegion(height, width)
            balances[count] = self.calcHeapOfBalances(center_region, data)
            break
        
        return balances
