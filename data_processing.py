import numpy as np
import math
import h5netcdf

from containers import Region, Id, Grid, Cell, RegionData


class DataLoader():
    """Класс для загрузки данных"""


class Coordinates():
    """Класс для работы с координатами"""

    def __init__(self, region: Region) -> None:
        """Инициализация"""

        # метров в одном градусе широты (по вертикали)
        self.LAT_DEGREE_LENGTH_METERS = 111 * 1e3
        # ячейки с шагом 0.25 градуса
        self.COEF = 4

        # расчет сетки
        self.STD_WIDTH = 1440
        self.STD_HEIGTH = 720    
        self.OPT_IMAGE_TOP0 = True

        self._region: Region = region

        self._grid: Grid = self._getGrid()
        self._id = self.getId(self._grid)
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

    def getId(self, grid: Grid) -> Id:
        """
        Рассчитывает краевые значение региона в индексах и возвращает результат
        """

        left = self.closestId(self._region.left, grid.lon)
        right = self.closestId(self._region.right, grid.lon)
        down = self.closestId(self._region.down, grid.lat)
        up = self.closestId(self._region.up, grid.lat)

        id = Id(left=left, right=right, down=down, up=up)
        return id
    
    def _getGrid(self) -> Grid:
        """Рассчитывает сетку координат и возвращает результат"""
        STD_lons =  [
            (20.125 + X * 0.25) if X<640 else (20.125 + (X - 1440) * 0.25) for X in range(self.STD_WIDTH)
        ]

        STD_lats_Btm0 = [ 89.875 - (719 - Y) * 0.25 for Y in range(self.STD_HEIGTH) ]
        STD_lats_Top0 = [ (719 - Y) * 0.25 - 89.875 for Y in range(self.STD_HEIGTH) ]
        STD_lats = STD_lats_Top0 if self.OPT_IMAGE_TOP0 else STD_lats_Btm0

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
            id=self._id,
            grid_region=self.grid_region,
            cell=self.cell,
        )

        return data
