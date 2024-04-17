import numpy as np
import pandas as pd
import pytest
import os
from datetime import datetime

from src.data_loading import DataLoader
from src.data_processing import BalanceCalculator
from src.containers import Region


# ---------- SETTINGS ----------

START_DAY = datetime(2022, 7, 10)
END_DAY = datetime(2022, 8, 9)

REGION = Region(55, 65, 130, 140)

DATA_PATH = "../CO_flow_2022.nc"
TARGET_VARIABLE_NAME = "20220601_mean"

# ------------------------------

SOURCE_DIR = "source"
EPSILON = 8e15

def calcBalance() -> np.ndarray:
    """Рассчитывает баланс"""
    data = DataLoader(DATA_PATH, TARGET_VARIABLE_NAME)
    data.setDateRange(START_DAY, END_DAY)

    bal_calc = BalanceCalculator()
    balance_data = bal_calc.calcRegionBalance(REGION, data)

    balance = balance_data.balance
    data.close()

    return balance


def loadBalance() -> np.ndarray:
    """Загружает эталонный баланс, рассчитанный с помощью программы Втюрина"""
    file_name = "test_region_balance.xlsx"
    file_path = os.path.join(SOURCE_DIR, file_name)

    df = pd.read_excel(file_path)
    balance = df["balance"].to_numpy()

    return balance

def test_calcRegionBalance() -> None:
    """
    Тестирование метода BalanceCalculator.calcRegionBalance()

    Тестирование проводится методом  сравнения  полученного  временного  ряда  баланса  с
    данными, полученными с помощью программы Втюрина
    """
    calculated_balance = calcBalance()
    etalon_balance = loadBalance()

    assert calculated_balance.ndim == 1, "Ряд должен быть одномерным"
    assert calculated_balance.shape == etalon_balance.shape, "Ряды должны иметь одинаковую размерность"

    mse = (np.square(calculated_balance - etalon_balance)).mean()
    assert mse < EPSILON, f"MSE должно быть меньше {EPSILON}"
