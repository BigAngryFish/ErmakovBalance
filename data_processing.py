import numpy as np
import math
import h5netcdf

from containers import Region, Id, Grid, Cell, RegionData


class DataLoader():
    """Класс для загрузки данных"""


class Coordinates():
    """Класс для работы с координатами"""

    def __init__(self, region: Region, grid: Grid) -> None:
        """Инициализация"""

        # метров в одном градусе широты (по вертикали)
        self.LAT_DEGREE_LENGTH_METERS = 111 * 1e3
        # ячейки с шагом 0.25 градуса
        self.COEF = 4

        self._region: Region = region
        self._grid: Grid = grid

        self._grid_region: Region = self._getGridRegion()
        self._cell: Cell = self._getCell()
    
    @property
    def id(self) -> Id:
        """Возвращает краевые значения региона в индексах"""
        return self._id
    
    @property
    def grid_region(self) -> Region:
        """Возвращает регион в координатах сетки"""
        return self._grid_region
    
    @property
    def cell(self) -> Region:
        """Возвращает размеры краевых ячеек в метрах"""
        return self._grid_region
    
    @staticmethod
    def closestId(coord: float, array: np.array) -> int:
        """
        Возвращает индекс значения из массива 'array',ближайшего по значению к координате
        'coord'
        """
        return np.argmin(array - coord)
    
    @staticmethod
    def closest(coord: float, array: np.array) -> float:
        """
        Возвращает значение из массива 'array', ближайшее к координате 'coord'
        """
        return np.argmin(array - coord)

    @staticmethod
    def calcLatCoef(lat_coord: int) -> float:
        """
        Рассчитывает коеффициент для вычисления длины параллели ячейки (длиной в четверть
        градуса) в зависимости от широты

        :param lat_coord: координата широты
        """
        return math.cos(math.radians(abs(lat_coord)))

    def getId(self) -> Id:
        """
        Рассчитывает краевые значение региона в индексах и возвращает результат
        """

        left = self.closestId(self._region.left, self._grid.lon)
        right = self.closestId(self._region.right, self._grid.lon)
        down = self.closestId(self._region.down, self._grid.lat)
        up = self.closestId(self._region.up, self._grid.lat)

        id = Id(left=left, right=right, down=down, up=up)
        return id
    
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
        length = self.LAT_DEGREE_LENGTH_METERS * coef / self.COEF
        return length


    def _getCell(self) -> Cell:
        """
        Рассчитывает параметры краевых ячеек в метрах и возвращает результат
        """
        height = self.LAT_DEGREE_LENGTH_METERS / self.COEF

        up = self.caclParralelLength(self._grid_region.up)
        down = self.caclParralelLength(self._grid_region.down)

        cell = Cell(left=height, right=height, down=down, up=up)
        return cell
    
    def getRegionData(self) -> RegionData:
        """Возвращает контейнер с основными данными региона"""

        data = RegionData(
            region=self._region,
            grid_region=self.grid_region,
            cell=self.cell,
        )

        return data
