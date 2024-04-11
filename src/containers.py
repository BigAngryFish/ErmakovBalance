from __future__ import annotations

import numpy as np
import pandas as pd
import h5netcdf

from dataclasses import dataclass
from datetime import datetime


class Region:
    """Класс для хранения координат региона"""

    def __init__(self, down: float, up: float, left: float, right: float) -> None:
        """Инициализация"""
        self._lat = np.asarray([down, up], dtype=np.float32)
        self._lon = np.asarray([left, right], dtype=np.float32)

    def __repr__(self) -> str:
        """Представление"""
        coords = f"down={self.down}, up={self.up}, left={self.left}, right={self.right}"
        return f"{self.__class__.__name__}({coords})"

    @property
    def down(self) -> float:
        return float(self._lat[0])
    
    @property
    def up(self) -> float:
        return float(self._lat[1])

    @property
    def left(self) -> float:
        return float(self._lon[0])

    @property
    def right(self) -> float:
        return float(self._lon[1])
    
    @property
    def lat(self) -> np.ndarray:
        return self._lat

    @property
    def lon(self) -> np.ndarray:
        return self._lon
    
    @property
    def height(self) -> float:
        return float(np.abs(self.up - self.down))

    @property
    def width(self) -> float:
        return float(np.abs(self.left - self.right))
    
    @property
    def coords(self) -> np.ndarray:
        """
        Возвращает координаты в одном двумерном массиве в формате
        array[[down, up], [left, right]]
        """
        return np.vstack((self._lat, self._lon))
    
    @property
    def center(self) -> np.ndarray:
        return np.mean(self.coords, axis=1)

    @staticmethod
    def fromNumpy(lat: np.ndarray, lon: np.ndarray) -> Region:
        """Десериализация  из массивов numpy"""
        down, up = map(float, lat)
        left, right = map(float, lon)
        return Region(down, up, left, right)
    
    def toNumpy(self) -> tuple[np.ndarray]:
        return self._lat, self._lon
    
    def addCoords(self, lat_value: float, lon_value: float) -> Region:
        lat = self._lat + lat_value
        lon = self._lon + lon_value
        return Region.fromNumpy(lat, lon)
    
    @staticmethod
    def regionAroundCenter(center: np.ndarray, height: float, width: float) -> Region:
        """
        Создает регион высотой  'height',  шириной  'width',  центр  которого находится в
        точке 'center', и возвращает результат
        """
        half_height, half_width = height / 2, width / 2 
        central_lat, central_lon = center
        lat = np.array([central_lat - half_height, central_lat + half_height])
        lon = np.array([central_lon - half_width, central_lon + half_width])
        return Region.fromNumpy(lat, lon)

    def centralizeRegion(self, height: float, width: float) -> Region:
        """
        Создает регион высотой  'height',  шириной  'width',  центр  которого совпадает с
        центром данного региона, и возвращает результат
        """
        return self.regionAroundCenter(self.center, height, width)
    

@dataclass
class Id:
    """
    Класс для хранения координат региона
    
    Хранит  индексы  координат  в  соответствующих  массивах  сетки.   Например,   индекс
    координаты наиболее близкой по значению широты в массиве с широтами сетки.
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
        - оригинальные координаты региона, заданные пользователем
    grid_region: Region
        - значения координат сетки, наиболее близкие к оригинальным координатам региона
    id: Id
        - индексы координат региона в базе данных
    cell: Cell
        - длины сторон крайних клеток
    cellareas: np.ndarray
        - площади каждой ячеки в регионе
    """
    region: Region
    grid_region: Region
    id: Id
    cell: Cell
    cellareas: np.ndarray


@dataclass
class Data():
    target: h5netcdf.Variable
    U: h5netcdf.Variable
    V: h5netcdf.Variable


@dataclass
class ConvData():
    """Содержит трехмерные массивы - широта, долгота, и время"""
    target: np.ndarray
    U: np.ndarray
    V: np.ndarray


@dataclass
class ConvConc():
    right: np.ndarray
    left: np.ndarray
    down: np.ndarray
    up: np.ndarray


@dataclass
class ConvFlow():
    right: np.ndarray
    left: np.ndarray
    down: np.ndarray
    up: np.ndarray


@dataclass
class ConvOriginalDayData():
    conc: ConvConc
    flow: ConvFlow


@dataclass
class ConvValue():
    right: np.ndarray
    left: np.ndarray
    down: np.ndarray
    up: np.ndarray


@dataclass
class DateRange():

    start: datetime
    end: datetime

    start_id: int
    end_id: int

    seconds: int

    time_series: pd.Series

    def __post_init__(self) -> None:
        """Рассчитываемые аттрибуты"""
        # единиц времени
        self.timesize = self.end_id - self.start_id + 1
