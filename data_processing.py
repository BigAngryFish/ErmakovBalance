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


class CoordTools():
    """Класс с функциями для работы с координатами"""

    @staticmethod
    def calcGrid() -> Grid:
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
    
    @staticmethod
    def caclParralelLength(lat_coord) -> float:
        """
        Рассчитывает  длину  единичного  отрезка  параллели  (0.25  градуса)  в  метрах и
        возвращает результат
        """
        coef = CoordTools.calcLatCoef(lat_coord)
        length = CELL_LENGTH_METERS * coef
        return length


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

        self._grid: Grid = grid if grid else CoordTools.calcGrid()
        self._id: Id = self.getId(self._region, self._grid)
        self._grid_region: Region = self.getGridRegion(self._region, self._grid)
        self._cell: Cell = self.getCell(self._grid_region)

        self.areas_matrix: np.ndarray = self.calcAreasMatrix(self._grid_region)
    
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
    def getId(region: Region, grid: Grid) -> Id:
        """
        Рассчитывает краевые значение региона в индексах и возвращает результат
        """
        left = CoordTools.closestId(region.left, grid.lon)
        right = CoordTools.closestId(region.right, grid.lon)
        down = CoordTools.closestId(region.down, grid.lat)
        up = CoordTools.closestId(region.up, grid.lat)

        id = Id(left=left, right=right, down=down, up=up)
        return id
    
    @staticmethod
    def getGridRegion(region: Region, grid: Grid) -> Region:
        """
        Изменяет координаты региона на ближайшие значения сетки и возвращает результат
        """
        left = CoordTools.closest(region.left, grid.lon)
        right = CoordTools.closest(region.right, grid.lon)
        down = CoordTools.closest(region.down, grid.lat)
        up = CoordTools.closest(region.up, grid.lat)

        grid_region = Region(left=left, right=right, down=down, up=up)
        return grid_region

    @staticmethod
    def getCell(grid_region: Region) -> Cell:
        """
        Рассчитывает параметры краевых ячеек в метрах и возвращает результат
        """
        up = CoordTools.caclParralelLength(grid_region.up)
        down = CoordTools.caclParralelLength(grid_region.down)

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

    @staticmethod
    def calcAreasMatrix(grid_region: Region) -> np.ndarray:
        """
        Расчитывает матрицу площадей ячеек региона

        Считается, что каждая ячейка имеет прямоугольную форму
        """
        height: int = int((grid_region.up - grid_region.down) // CELL_STEP + 1)
        width: int = int((grid_region.right - grid_region.left) // CELL_STEP + 1)

        up: float = grid_region.up
        areas: np.ndarray = np.zeros((height, width))
        cell_area: float

        for row in range(height):
            cell_area = pow(CELL_LENGTH_METERS, 2) * CoordTools.calcLatCoef(abs(up))
            areas[row] += cell_area
            up -= CELL_STEP
    
        return areas

    def calcSum(self, map: np.ndarray) -> float:
        """
        Рассчитывает сумму в регионе и возвращает результат

        Значение концетрации в точке для каждой ячейки  интерполируется  на  всю  площадь
        ячейки, после чего суммируется содержание по всей площади ячейки
        
        :param map: 2D-numpy.ndarray размером (STD_HEIGTH,STD_WIDTH), карта с содержанием
            газа в точке внутри каждой ячейки
        :type map: numpy.ndarray
        """
        values_in_points: np.ndarray = (
            np.transpose(map)[
                self.id.up : self.id.down + 1,
                self.id.left : self.id.right + 1
            ]
        )

        sum_per_cell: np.ndarray = self.areas_matrix * values_in_points
        total_sum: float = float(sum_per_cell.sum())

        return total_sum

    def calcConv(self, data: Data) -> float:
        """Рассчитывает дивергенцию в регионе и возвращает результат"""
