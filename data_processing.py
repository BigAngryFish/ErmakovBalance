import numpy as np
import math

from containers import *
from constants import *


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
        return int(np.argmin(np.absolute(array - coord)))
    
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

    # def getConvConc(self, target_map: np.ndarray) -> ConvConc:
    #     """Вовращает граничные массивы концетрация"""
    #     self._verifyMap(target_map)

    #     # концентрация по границам (кг / м2)
    #     right_conc = target_map[self.id.up : self.id.down + 1, self.id.right]
    #     left_conc = target_map[self.id.up : self.id.down + 1, self.id.left]
    #     down_conc = target_map[self.id.down, self.id.left : self.id.right + 1]
    #     up_conc = target_map[self.id.up, self.id.left : self.id.right + 1]

    #     conv_conc = ConvConc(
    #         right=right_conc,
    #         left=left_conc,
    #         down=down_conc,
    #         up=up_conc,
    #     )

    #     return conv_conc
    
    # def getConvFlow(self, umap: np.ndarray, vmap: np.ndarray) -> ConvFlow:
    #     """Возвращает граничные значения перемещений"""
    #     self._verifyMap(umap)
    #     self._verifyMap(vmap)

    #     # U по границам (м / с)
    #     right_flow = umap[self.id.up : self.id.down + 1, self.id.right]
    #     left_flow = umap[self.id.up : self.id.down + 1, self.id.left]
    #     # V по границам  (м / с)
    #     down_flow = vmap[self.id.down, self.id.left : self.id.right + 1]
    #     up_flow = vmap[self.id.up, self.id.left : self.id.right + 1]

    #     flow = ConvFlow(
    #         right=right_flow,
    #         left=left_flow,
    #         down=down_flow,
    #         up=up_flow,
    #     )

    #     return flow
    

    # def calcConv(self, data: ConvData, mode: str = "total") -> float | tuple:
    #     """
    #     Рассчитывает дивергенцию в регионе и возвращает результат
        
    #     Рассчет ведется для одной единицы  времени,  соответственно  карты  концентрации,
    #     вертикальный и горизонтальных перемещений представляют собой двумерные массивы
        
    #     :param data: карты концентрации и перемещений вещества
    #     :type data: ConvData
    #     :param mode: ["total", "diff"]  -  определяет  тип  возвращаемого  значения; если
    #         "total"  -  возвращается суммарное значение переноса вещества в регионе, если
    #         "diff" - кортеж (income, outcome) со значениями вноса и выноса вещества
    #     """
    #     self._verifyConvData(data)

    #     conc = self.getConvConc(data.target)
    #     flow = self.getConvFlow(umap=data.U, vmap=data.V)
    #     values = self.getConvValue(conc, flow)

    #     income = self.calcIncome(values)
    #     outcome = self.calcOutcome(values)

    #     if mode == "diff":
    #         return income, outcome
        
    #     elif mode == "total":
    #         return (income - outcome) * 3 * 3600
        
    #     else:
    #         raise ValueError("invalid 'mode'")        


class ConvCalculator():
    #TODO секунды - затычка
    def __init__(self, region_cell: Cell, seconds: int = 3 * 3600) -> None:
        """Инициализация"""

        self.cell: Cell = region_cell
        self.seconds: int = seconds
    
    def getConvValue(self, conc: ConvConc, flow: ConvFlow) -> ConvValue:
        """Рассчитывает потоки через границы"""
        # значение унесенного/ принесенного вещества (кг / м2) * (м / c) * м
        right_value_flow = conc.right * flow.right * self.cell.right
        left_value_flow = conc.left * flow.left * self.cell.left
        down_value_flow = conc.down * flow.down * self.cell.down
        up_value_flow = conc.up * flow.up * self.cell.up

        values = ConvValue(
            right=right_value_flow,
            left=left_value_flow,
            down=down_value_flow,
            up=up_value_flow,
        )

        return values
    
    @staticmethod
    def calcIncome(conv_values: ConvValue) -> float:
        """Рассчитывает приход"""
        income = float(
            conv_values.right[np.argwhere(conv_values.right < 0)].sum() * -1
            + conv_values.left[np.argwhere(conv_values.left > 0)].sum()
            + conv_values.down[np.argwhere(conv_values.down > 0)].sum()
            + conv_values.up[np.argwhere(conv_values.up < 0)].sum() * -1
        )
        return income

    @staticmethod
    def calcOutcome(conv_values: ConvValue) -> float:
        """Рассчитывает уход"""
        outcome = float(
            conv_values.right[np.argwhere(conv_values.right >= 0)].sum()
            + conv_values.left[np.argwhere(conv_values.left <= 0)].sum() * -1
            + conv_values.down[np.argwhere(conv_values.down <= 0)].sum() * -1
            + conv_values.up[np.argwhere(conv_values.up >= 0)].sum()
        )
        return outcome

    def pipeline(self, convdata: ConvOriginalDayData, mode: str = "total") -> float | tuple:
        """Рассчитывает конвергенция в регионе для одного дня"""
        values = self.getConvValue(convdata.conc, convdata.flow)

        income = self.calcIncome(values) * self.seconds
        outcome = self.calcOutcome(values) * self.seconds

        if mode == "diff":
            return income, outcome
        
        elif mode == "total":
            return (income - outcome)
        
        else:
            raise ValueError("invalid 'mode'") 

    def __call__(self, convdata: ConvOriginalDayData, mode: str = "total") -> float | tuple:
        return self.pipeline(convdata, mode)
