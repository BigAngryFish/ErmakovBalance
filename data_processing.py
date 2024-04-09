import numpy as np
import math
import h5netcdf
from datetime import date, datetime

from containers import Region, Id, Grid, Cell, RegionData, Data, ConvData, DateData, ConvDayData
from constants import *


class DataLoader():
    """Класс для загрузки данных"""

    def __init__(self, path: str, target_name: str) -> None:
        """Инициализация"""

        self._db: h5netcdf.File = h5netcdf.File(path, "r")
        self.target_name: str = target_name

        self.original_shape = self._db[target_name].shape
        self.transposed_shape = (
            self.original_shape[1],
            self.original_shape[0],
            self.original_shape[2],
        )

        self.region_id: Id = self.getDefaultRegionRange()
        self.date_data: DateData = self.getDefaultDateRange()

    @property
    def convdata(self) -> ConvData:
        """Возвращает извлеченные данные"""
        return self.getRegionData()
    
    @property
    def timedim(self) -> int:
        """Возвращает количество единиц времени"""
        return self.date_data.end_id - self.date_data.start_id
    
    def getRegionData(self) -> ConvData:
        """Извлекает необходимые данные из БД"""

        target: h5netcdf.Variable = self._db[self.target_name]
        target_arr = target[
            self.region_id.left : self.region_id.right + 1,
            self.region_id.up : self.region_id.down + 1,
            self.date_data.start_id : self.date_data.end_id,
        ]

        U: h5netcdf.Variable = self._db["U"]
        U_arr = U[
            self.region_id.left : self.region_id.right + 1,
            self.region_id.up : self.region_id.down + 1,
            self.date_data.start_id : self.date_data.end_id,
        ]

        V: h5netcdf.Variable = self._db["V"]
        V_arr = V[
            self.region_id.left : self.region_id.right + 1,
            self.region_id.up : self.region_id.down + 1,
            self.date_data.start_id : self.date_data.end_id,
        ]

        data = ConvData(target=target_arr, U=U_arr, V=V_arr)
        return data
    
    def getTargetMap(self, day_id: int) -> np.ndarray:
        data_map = self._db[self.target_name][..., day_id]
        return np.transpose(data_map)
    
    def getUMap(self, day_id: int) -> np.ndarray:
        return np.transpose(self._db["U"][..., day_id])
    
    def getVMap(self, day_id: int) -> np.ndarray:
        return np.transpose(self._db["V"][..., day_id])
    
    def getRegionDayData(self, day_id: int) -> ConvDayData:
        """Извлекает необходимые данные из БД"""

        target: h5netcdf.Variable = self._db[self.target_name]
        target_arr = target[
            self.region_id.left : self.region_id.right + 1,
            self.region_id.up : self.region_id.down + 1,
            day_id,
        ]

        U: h5netcdf.Variable = self._db["U"]
        U_arr = U[
            self.region_id.left : self.region_id.right + 1,
            self.region_id.up : self.region_id.down + 1,
            day_id,
        ]

        V: h5netcdf.Variable = self._db["V"]
        V_arr = V[
            self.region_id.left : self.region_id.right + 1,
            self.region_id.up : self.region_id.down + 1,
            day_id,
        ]

        data = ConvDayData(target=target_arr, U=U_arr, V=V_arr)
        return data
    
    def setRegionId(self, region_id: Id | None) -> None:
        self.region_id = region_id
    
    def setDateRange(self, date_range: tuple[date, date]) -> None:
        pass

    def getDefaultDateRange(self) -> DateData:
        """Вычисляет дефолтный временной диапазон"""
        start_id = 0
        end_id = self.original_shape[2] - 1

        start_day = self._stimeToDate(self._db["stime"][start_id])
        end_day = self._stimeToDate(self._db["stime"][end_id])

        next_day = self._stimeToDate(self._db["stime"][start_id + 1])
        seconds = (next_day - start_day).seconds

        date_data = DateData(
            start=start_day, end=end_day,
            start_id=start_id, end_id=end_id,
            seconds=seconds,
        )

        return date_data
    
    def getDefaultRegionRange(self) -> Id:
        """Дефолтный регион - вся область"""
        region_id = Id(
            left=0,
            right=self.original_shape[1],
            up=0,
            down=self.original_shape[0],
        )
        return region_id

    @staticmethod
    def _stimeToDate(stime: bytes) -> datetime:
        stime = str(stime)
        day_values = list(map(int, stime[2:12].split('-')))
        year, month, day = day_values
        hour = int(stime[13:15])
        day = datetime(year=year, month=month, day=day, hour=hour)

        return day
    
    def dayonvData(day: date) -> ConvData:
        """Возвращает данные для определенного дня"""
        pass
    
    def close(self) -> None:
        """Закрытие базы данных"""
        self._db.close()


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
        left = CoordTools.closestId(region.left, grid.lon) + 1
        right = CoordTools.closestId(region.right, grid.lon) + 1
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

    @staticmethod    
    def _verifyMap(data_map: np.ndarray) -> None:
        """"Проверяет размерность карты"""

        if not isinstance(data_map, np.ndarray):
            raise TypeError(f"expected numpy.ndarray for 'data_map")

        if data_map.ndim != 2:
            raise TypeError(f"expected 2D array for 'data_map'")

        if data_map.shape != MAP_SIZE:    
            raise ValueError(f"'data_map' must have shape of {MAP_SIZE}")


    def calcSum(self, data_map: np.ndarray) -> float:
        """
        Рассчитывает сумму в регионе и возвращает результат

        Значение концетрации в точке для каждой ячейки  интерполируется  на  всю  площадь
        ячейки, после чего суммируется содержание по всей площади ячейки
        
        :param data_map: 2D-numpy.ndarray размером (STD_HEIGTH,STD_WIDTH), карта с содержанием
            газа в точке внутри каждой ячейки
        :type data_map: numpy.ndarray
        """
        self._verifyMap(data_map)

        values_in_points: np.ndarray = data_map[
            self.id.up : self.id.down + 1,
            self.id.left : self.id.right + 1
        ]

        total_sum = (self.areas_matrix * values_in_points).sum()
        return float(total_sum)
    
    def _verifyConvData(self, data: ConvData) -> None:
        """Проверяет валидность ConvData"""
        self._verifyMap(data.target)
        self._verifyMap(data.U)
        self._verifyMap(data.V)

    def calcConv(self, data: ConvData, mode: str = "total") -> float | tuple:
        """
        Рассчитывает дивергенцию в регионе и возвращает результат
        
        Рассчет ведется для одной единицы  времени,  соответственно  карты  концентрации,
        вертикальный и горизонтальных перемещений представляют собой двумерные массивы
        
        :param data: карты концентрации и перемещений вещества
        :type data: ConvData
        :param mode: ["total", "diff"]  -  определяет  тип  возвращаемого  значения; если
            "total"  -  возвращается суммарное значение переноса вещества в регионе, если
            "diff" - кортеж (income, outcome) со значениями вноса и выноса вещества
        """
        self._verifyConvData(data)

        # концентрация по границам (кг / м2)
        right_conc = data.target[self.id.up : self.id.down + 1, self.id.right]
        left_conc = data.target[self.id.up : self.id.down + 1, self.id.left]
        down_conc = data.target[self.id.down, self.id.left : self.id.right + 1]
        up_conc = data.target[self.id.up, self.id.left : self.id.right + 1]

        # U по границам (м / с)
        right_flow = data.U[self.id.up : self.id.down + 1, self.id.right]
        left_flow = data.U[self.id.up : self.id.down + 1, self.id.left]
        # V по границам  (м / с)
        down_flow = data.V[self.id.down, self.id.left : self.id.right + 1]
        up_flow = data.V[self.id.up, self.id.left : self.id.right + 1]

        # значение унесенного/ принесенного вещества (кг / м2) * (м / c) * м
        right_value_flow = right_conc * right_flow * self.cell.right
        left_value_flow = left_conc * left_flow * self.cell.left
        down_value_flow = down_conc * down_flow * self.cell.down
        up_value_flow = up_conc * up_flow * self.cell.up

        income = float(
            right_value_flow[np.argwhere(right_value_flow < 0)].sum() * -1
            + left_value_flow[np.argwhere(left_value_flow > 0)].sum()
            + down_value_flow[np.argwhere(down_value_flow > 0)].sum()
            + up_value_flow[np.argwhere(up_value_flow < 0)].sum() * -1
        )

        outcome = float(
            right_value_flow[np.argwhere(right_value_flow >= 0)].sum()
            + left_value_flow[np.argwhere(left_value_flow <= 0)].sum() * -1
            + down_value_flow[np.argwhere(down_value_flow <= 0)].sum() * -1
            + up_value_flow[np.argwhere(up_value_flow >= 0)].sum()
        )

        if mode == "diff":
            return income, outcome
        
        elif mode == "total":
            return (income - outcome) * 3 * 3600
        
        else:
            raise ValueError("invalid 'mode'")        
