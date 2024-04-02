import numpy as np
import math

from dataclasses import dataclass


@dataclass
class Region:
    """Класс для хранения координат региона"""
    down: float
    up: float
    right: float
    left: float


@dataclass
class Id:
    """
    Класс для хранения координат региона
    
    Хранит  индексы  координат  в  соответствующих  массивах  сетки.   Например,   индекс
    координаты максимальной широты в массиве с широтами сетки.
    """
    down: int 
    up: int
    left: int
    right: int


@dataclass
class Grid:
    # все значения координат широт в сетке
    lat: np.ndarray
    # все значения координат долгот в сетке
    lon: np.ndarray


@dataclass
class Cell:
    """
    Контейнер для хранения единичных длин границ региона

    То есть, длина верхней границы верхних ячеек, длина левой границы левых ячеек,  длина
    нижней границы нижних ячеек, длина правой границы крайних правых ячеек
    """
    down: float
    up: float
    left: float
    right: float


@dataclass
class RegionData():
    """
    Контейнер для хранения координатных данных региона

    Атрибуты:
    ---------
    region: Region
    grid_region: Region
    id: Id
    cell: Cell
    """

    region: Region
    grid_region: Region
    id: Id
    cell: Cell


@dataclass
class Data():
    target: np.ndarray
    U: np.ndarray | None = None
    V: np.ndarray | None = None
