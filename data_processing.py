import numpy as np
import math
import h5netcdf

from containers import Region, Id, Grid, Cell, RegionData, Data
from constants import *


class DataLoader():
    """Класс для загрузки данных"""

    def __init__(self, path: str, target: str) -> None:
        """Инициализация"""

        self._db: h5netcdf.File = h5netcdf.File(path, "r")
        self._data: Data = self.extractData(self._db, target)
        self._db.close()

    @property
    def data(self) -> Data:
        """Возвращает извлеченные данные"""
        return self._data
    
    @staticmethod
    def extractData(db: h5netcdf.File, target_name: str) -> Data:
        """Извлекает необходимые данные из БД"""

        target = np.array(db[target_name][..., 0])
        # U = np.array(db["U"])
        # V = np.array(db["V"])

        data = Data(target=target)
        return data


class RegionProcessor():
    """
    Класс для работы с координатами
    
    Параметры:
    ----------
    region: Region
        координаты обсчитываемого региона

    grid: Grid | None
        координатная сетка; если аргумент не передан, сетка рассчитывается самостоятельно
    """

    def __init__(self, region: Region, grid: Grid | None = None) -> None:
        """
        Инициализация
        
        :param region: координаты обсчитываемого региона
        :type region: Region
        :param grid: координатная сетка; если аргумент не передан,  сетка рассчитывается
            самостоятельно
        :grid type: Grid
        """

        self._region: Region = region

        self._grid: Grid = grid if grid else self._calcGrid()
        self._id: Id = self.getId(self._region, self._grid)
        self._grid_region: Region = self._getGridRegion()
        self._cell: Cell = self._getCell()
    
    @property
    def id(self) -> Id:
        """Возвращает краевые значения региона в индексах"""
        return self._id
    
    @property
    def grid(self) -> Grid:
        """Возвращает координатную сетку"""
        return self._grid
    
    @property
    def grid_region(self) -> Region:
        """Возвращает регион в координатах сетки"""
        return self._grid_region
    
    @property
    def cell(self) -> Region:
        """Возвращает размеры краевых ячеек в метрах"""
        return self._cell
    
    @staticmethod
    def closestId(coord: float, array: np.array) -> int:
        """
        Возвращает индекс значения из массива 'array',ближайшего по значению к координате
        'coord'
        """
        return np.argmin(np.absolute(array - coord))
    
    @staticmethod
    def closest(coord: float, array: np.array) -> float:
        """
        Возвращает значение из массива 'array', ближайшее к координате 'coord'
        """
        return float(array[np.argmin(np.absolute(array - coord))])

    @staticmethod
    def calcLatCoef(lat_coord: int) -> float:
        """
        Рассчитывает коеффициент для вычисления длины параллели ячейки (длиной в четверть
        градуса) в зависимости от широты

        :param lat_coord: координата широты
        """
        return math.cos(math.radians(abs(lat_coord)))
    
    def calcArea(self, grid_region: Region, id: Id) -> float:
        """
        Расчитывает матрицу площадей ячеек

        Считается, что каждая ячейка имеет прямоугольную форму
        """
        height = id.down - id.up + 1
        width = id.right - id.left + 1

        areas = []
        up = grid_region.up
    
        # TODO: оптимизировать
        for _ in range(height):
            cell_area = pow(CELL_LENGTH_METERS, 2) * self.calcLatCoef(abs(up))
            row_areas = [cell_area] * width
            areas.append(row_areas)
            up -= 0.25
        areas = np.array(areas)
    
        return areas

    def getId(self, region: Region, grid: Grid) -> Id:
        """
        Рассчитывает краевые значение региона в индексах и возвращает результат
        """

        left = self.closestId(region.left, grid.lon)
        right = self.closestId(region.right, grid.lon)
        down = self.closestId(region.down, grid.lat)
        up = self.closestId(region.up, grid.lat)

        id = Id(left=left, right=right, down=down, up=up)
        return id
    
    def _calcGrid(self) -> Grid:
        """Рассчитывает сетку координат и возвращает результат"""
        STD_lons =  [
            (20.125 + X * 0.25) if X<640 else (20.125 + (X - 1440) * 0.25) for X in range(STD_WIDTH)
        ]

        STD_lats_Btm0 = [ 89.875 - (719 - Y) * 0.25 for Y in range(STD_HEIGTH) ]
        STD_lats_Top0 = [ (719 - Y) * 0.25 - 89.875 for Y in range(STD_HEIGTH) ]
        STD_lats = STD_lats_Top0 if OPT_IMAGE_TOP0 else STD_lats_Btm0

        grid = Grid(
            lat=np.array(STD_lats), 
            lon=np.array(STD_lons),
        )
    
        return grid

    def _getGridRegion(self) -> Region:
        """
        Изменяет координаты региона на ближайшие значения сетки и возвращает результат
        """

        left = self.closest(self._region.left, self._grid.lon)
        right = self.closest(self._region.right, self._grid.lon)
        down = self.closest(self._region.down, self._grid.lat)
        up = self.closest(self._region.up, self._grid.lat)

        region = Region(left=left, right=right, down=down, up=up)
        return region

    def caclParralelLength(self, lat_coord) -> float:
        """
        Рассчитывает  длину  единичного  отрезка  параллели  (0.25  градуса)  в  метрах и
        возвращает результат
        """
        coef = self.calcLatCoef(lat_coord)
        length = CELL_LENGTH_METERS * coef
        return length

    def _getCell(self) -> Cell:
        """
        Рассчитывает параметры краевых ячеек в метрах и возвращает результат
        """
        up = self.caclParralelLength(self._grid_region.up)
        down = self.caclParralelLength(self._grid_region.down)

        cell = Cell(left=CELL_LENGTH_METERS, right=CELL_LENGTH_METERS, down=down, up=up)
        return cell

    def getRegionData(self) -> RegionData:
        """Возвращает контейнер с основными данными региона"""

        data = RegionData(
            region=self._region,
            id=self._id,
            grid_region=self.grid_region,
            cell=self.cell,
        )

        return data

    def calcSum(self, data: Data) -> float:
        """Рассчитывает сумму в регионе и возвращает результат"""

        areas = self.calcArea(self.grid_region, self.id)
        values_in_points = (
            np.transpose(data.target)[
                self.id.up : self.id.down + 1,
                self.id.left : self.id.right + 1
            ]
        )
        # values_in_points = (
        #     np.transpose(data.target[...,0])[
        #         self.id.up : self.id.down + 1,
        #         self.id.left : self.id.right + 1
        #     ]
        # )

        sum_per_cell = areas * values_in_points
        total_sum = sum_per_cell.sum()

        return float(total_sum)

    def calcConv(self, data: Data) -> float:
        """Рассчитывает дивергенцию в регионе и возвращает результат"""
