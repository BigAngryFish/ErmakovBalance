import numpy as np

from tools import CoordTools, verifyMap
from data_loading import  DataLoader
from containers import *
from constants import *


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
    
    @property
    def areas(self) ->np.ndarray:
        """Возвращает площади ячеек в м2"""
        return self.areas_matrix
    
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
            cellareas=self.areas_matrix,
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


class SumCalculator():
    """
    Класс для расчета суммы содержания вещества в регионе в данный момент времени
    
    Параметры
    ---------
    regdata: RegionData
        пространственная информация о регионе    
    """

    def __init__(self, regdata: RegionData) -> None:
        """Инициализация"""

        self.regdata: RegionData = regdata

    def calcSum(self, data_map: np.ndarray) -> float:
        """
        Рассчитывает сумму в регионе и возвращает результат

        Значение концетрации в точке для каждой ячейки  интерполируется  на  всю  площадь
        ячейки, после чего суммируется содержание по всей площади ячейки
        
        :param data_map: 2D-numpy.ndarray размером (STD_HEIGTH,STD_WIDTH), карта с содержанием
            газа в точке внутри каждой ячейки
        :type data_map: numpy.ndarray
        ...
        :return: суммарное содержание вещества в регионе в данный момент времени (в кг)
        :rtype: float
        """
        verifyMap(data_map)

        region_id = self.regdata.id
        cellareas = self.regdata.cellareas

        values_in_points: np.ndarray = data_map[
            region_id.up : region_id.down + 1,
            region_id.left : region_id.right + 1
        ]

        total_sum = (cellareas * values_in_points).sum()
        return float(total_sum)
    
    def __call__(self, data_map: np.ndarray) -> float:
        return self.calcSum(data_map)


class ConvCalculator():
    #TODO секунды - затычка
    def __init__(self, regdata: RegionData, seconds: int = 3 * 3600) -> None:
        """Инициализация"""

        self.regdata: RegionData = regdata
        self.seconds: int = seconds
    
    def getConvValue(self, conc: ConvConc, flow: ConvFlow) -> ConvValue:
        """Рассчитывает потоки через границы"""
        cell = self.regdata.cell

        # значение унесенного/ принесенного вещества (кг / м2) * (м / c) * м
        right_value_flow = conc.right * flow.right * cell.right
        left_value_flow = conc.left * flow.left * cell.left
        down_value_flow = conc.down * flow.down * cell.down
        up_value_flow = conc.up * flow.up * cell.up

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

    def calcConv(self, convdata: ConvOriginalDayData, mode: str = "total") -> float | tuple:
        """
        Рассчитывает конвергенция в регионе для одного дня

        :param convdata: данные, необходимые для расчета конвергенции
        :type convdata: ConvOriginalDayData
        :param mode: ["total", "diff"]  -  определяет  тип  возвращаемого  значения; если
            "total"  -  возвращается суммарное значение переноса вещества в регионе, если
            "diff" - кортеж (income, outcome) со значениями вноса и выноса вещества
        :type mode: str
        """
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
        """
        Рассчитывает конвергенция в регионе для одного дня

        :param convdata: данные, необходимые для расчета конвергенции
        :type convdata: ConvOriginalDayData
        :param mode: ["total", "diff"]  -  определяет  тип  возвращаемого  значения; если
            "total"  -  возвращается суммарное значение переноса вещества в регионе, если
            "diff" - кортеж (income, outcome) со значениями вноса и выноса вещества
        :type mode: str
        """
        return self.calcConv(convdata, mode)



class BalanceCalculator():

    def __init__(self, regdata: RegionData, data_loader: DataLoader, date_range: tuple) -> None:
        """Инициализация"""

        self.regdata: RegionData = regdata
        self.data_loader: DataLoader = data_loader
        self.start_day, self.end_day = date_range
    
        self.sum_calculator = SumCalculator(self.regdata)
        self.conv_calculator = ConvCalculator(self.regdata)

    def calcSumSeries(self) -> np.ndarray:
        """Рассчитывает временной ряд сумм содержания вещества в регионе"""
        sums = np.zeros(self.end_day - self.start_day + 1)
    
        for day_id in range(self.start_day, self.end_day + 1):
            concmap = self.data_loader.getTargetMap(day_id)
            sums[day_id - self.start_day] = self.sum_calculator(concmap)
    
        return sums

    def calcSumsDiffSeries(self) -> np.ndarray:
        """Рассчитывает разницу сумм концетраций"""
        sums = self.calcSumSeries()

        sums_len = sums.size
        diff_sums_len = sums_len - 1

        diff_sums = np.zeros(diff_sums_len)
        for day_id in range(diff_sums_len):
            diff_sums[day_id] = sums[day_id + 1] - sums[day_id]

        return diff_sums
    
    def calcConvSeries(self) -> np.ndarray:
        """Рассчитывает разницу конвергенций"""
        # расчет конвергенции (для каждой единицы времени)
        convs = np.zeros(self.end_day - self.start_day + 1)

        for day_id in range(self.start_day, self.end_day + 1):
            convdata = self.data_loader.getConvData(day_id, self.regdata.id)
            convs[day_id - self.start_day] = self.conv_calculator(convdata)

        return convs

    @staticmethod
    def calcBalanceSeries(diff_sums: np.ndarray, convs: np.ndarray) -> np.ndarray:
        """
        Рассчитывает временной ряд баланса

        :param diff_sums:  временной ряд,  изменение в суммарном содержании  вещества  на
            единицу времени
        :type diff_sums: 1D массив numpy
        :param convs:  временной ряд,  конвергенция  вещества  через  границы  региона на
            единицу времени
        :type convs: 1D массив numpy
        """
        if diff_sums.ndim != convs.ndim != 1:
            raise ValueError("'diff_sums' and 'convs' must be 1-dimensional arrays")

        if diff_sums.size != convs.size:
            raise ValueError("'diff_summs' and 'convs' have different size")
        
        return diff_sums - convs

    def getBalanceSeries(self) -> np.ndarray:
        """Рассчитывает временной ряд баланса"""

        diff_sums = self.calcSumsDiffSeries()
        convs =self.calcConvSeries()

        convs = np.delete(convs, -1)
        balance = self.calcBalanceSeries(diff_sums, convs)

        return balance
