import numpy as np

from src.tools import CoordTools, Mode, verifyMap
from src.data_loading import  DataLoader, BalanceData
from src.containers import *
from src.constants import *


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

    @staticmethod
    def calcSum(data_map: np.ndarray, regdata: RegionData) -> float:
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

        region_id = regdata.id
        cellareas = regdata.cellareas

        values_in_points: np.ndarray = data_map[
            region_id.up : region_id.down + 1,
            region_id.left : region_id.right + 1
        ]

        total_sum = (cellareas * values_in_points).sum()
        return float(total_sum)
    
    def __call__(self, data_map: np.ndarray, regdata: RegionData) -> float:
        return self.calcSum(data_map, regdata)


class ConvCalculator():
    
    @staticmethod
    def getConvValue(conc: ConvConc, flow: ConvFlow, cell: Cell) -> ConvValue:
        """Рассчитывает потоки через границы"""
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

    def calcConv(self,
                 convdata: ConvOriginalDayData,
                 regdata: RegionData,
                 seconds: int,
                 mode: Mode = Mode.TOTAL,
                ) -> float | tuple:
        """
        Рассчитывает конвергенция в регионе для одного дня

        :param convdata: данные, необходимые для расчета конвергенции
        :type convdata: ConvOriginalDayData
        :param mode: [Mode.TOTAL, Mode.SEP]  -  определяет  тип  возвращаемого  значения; если
            Mode.TOTAL  -  возвращается суммарное значение переноса вещества в регионе, если
            Mode.SEP - кортеж (income, outcome) со значениями вноса и выноса вещества
        :type mode: Mode
        """
        values = self.getConvValue(convdata.conc, convdata.flow, regdata.cell)

        income = self.calcIncome(values) * seconds
        outcome = self.calcOutcome(values) * seconds

        if mode == Mode.SEP:
            return income, outcome
        
        elif mode == Mode.TOTAL:
            return (income - outcome)
        
        else:
            raise ValueError("invalid 'mode'") 

    def __call__(self,
                 convdata: ConvOriginalDayData,
                 regdata: RegionData,
                 seconds: int,
                 mode: Mode = Mode.TOTAL,
                ) -> float | tuple:
        """
        Рассчитывает конвергенция в регионе для одного дня

        :param convdata: данные, необходимые для расчета конвергенции
        :type convdata: ConvOriginalDayData
        :param mode: [Mode.TOTAL, Mode.SEP]  -  определяет  тип  возвращаемого  значения; если
            Mode.TOTAL  -  возвращается суммарное значение переноса вещества в регионе, если
            Mode.SEP - кортеж (income, outcome) со значениями вноса и выноса вещества
        :type mode: Mode
        """
        return self.calcConv(convdata, regdata, seconds, mode)


class BalanceCalculator():
    """
    Класс для расчета баланса

    Параметры:
    ----------
    regdata: RegionData
        - пространственная информация о регионе
    
    data_loader: DataLoader
        - исходные данные
    
    data_range: DataRange
        - временной диапазон расчета
    
    Методы:
    -------
    calcSumSeries() -> np.ndarray
        - рассчитывает временной ряд содержания вещества в атмосфере для заданных региона
        и промежутка времени и возвращает результат

    calcSumsDiffSeries() -> np.ndarray
        - рассчитывает временной ряд разницы содержания вещества в атмосфере для заданных
        региона и промежутка времени и возвращает результат
    
    calcConvSeries() -> np.ndarray
        - рассчитывает  временной  ряд  конвергенции  вещества  в  атмосфере для заданных
        региона и промежутка времени и возвращает результат
    
    getBalanceSeries() -> np.ndarray | pd.DataFrame
        - рассчитывает временной ряд баланса вещества  в атмосфере для заданных региона и
        промежутка времени и возвращает результат

    Примеры использования:
    ----------------------
    >>> balance_calculator = BalaceCalculator(regdata, data_loader, date_range)
    >>> balance = balance_calculator.getBalanceSeries()
    """

    def __init__(self) -> None:
        """Инициализация"""
        self.sum_calculator = SumCalculator()
        self.conv_calculator = ConvCalculator()
    
    @staticmethod
    def _verifyParams(regdata: RegionData, data_loader: DataLoader, date_range: DateRange) -> None:
        """Проверка аргументов"""

        if not isinstance(regdata, RegionData):
            raise ValueError(f"'regdata' must be RegionData instance, got {type(regdata)}")

        if not isinstance(data_loader, DataLoader):
            raise ValueError(f"'data_loader' must be DataLoader instance, got {type(data_loader)}")

        if not isinstance(date_range, DateRange):
            raise ValueError(f"'date_range' must be DateRange instance, got {type(date_range)}")

    def calcSumSeries(self, balance_data: BalanceData) -> np.ndarray:
        """Рассчитывает временной ряд сумм содержания вещества в регионе"""
    
        # данные, необходимые для расчета
        regdata = balance_data.reg_data
        data_loader = balance_data.data
        date_range = data_loader.date_range
    
        # рассчитываем на одно значение больше, потому что надо вычитать
        # каждое предыдущее из следующего, так что массив изменения массы
        # будет на 1 меньше
        start_id, end_id = date_range.start_id, date_range.end_id + 1
        sums = np.zeros(date_range.timesize + 1)
    
        for time_id in range(start_id, end_id + 1):
            concmap = data_loader.getTargetMap(time_id)
            sums[time_id - start_id] = self.sum_calculator(concmap, regdata)
    
        return sums

    @staticmethod
    def calcSumsDiffSeries(sums: np.ndarray) -> np.ndarray:
        """Рассчитывает разницу сумм концетраций"""
        # sums = self.calcSumSeries()

        sums_len = sums.size
        diff_sums_len = sums_len - 1

        diff_sums = np.zeros(diff_sums_len)
        for time_id in range(diff_sums_len):
            diff_sums[time_id] = sums[time_id + 1] - sums[time_id]

        return diff_sums
    
    def calcConvSeries(self, balance_data: BalanceData) -> np.ndarray:
        """Рассчитывает разницу конвергенций"""

        # данные, необходимые для расчета
        regdata = balance_data.reg_data
        data_loader = balance_data.data
        date_range = data_loader.date_range

        # расчет конвергенции (для каждой единицы времени)
        start_id, end_id = date_range.start_id, date_range.end_id
        convs = np.zeros(end_id - start_id + 1)

        for day_id in range(start_id, end_id + 1):
            convdata =data_loader.getConvData(day_id, regdata.id)
            convs[day_id - start_id] = self.conv_calculator(convdata, regdata, date_range.seconds)

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

    def makeBalanceDF(self, balance_series: np.ndarray) -> pd.DataFrame:
        """
        Возвращает временной ряд баласа в pandas.DataFrame
        
        Итоговой датафрейм содержит две колонки - "time" и "balance"
        """
        time_series = self.date_range.time_series

        if len(time_series) != balance_series.size:
            raise ValueError("'time' and 'balance' have different size")

        df = pd.DataFrame({"time" : time_series, "balance" : balance_series})
        # df.set_index("time", inplace=True)

        return df

    def getBalanceSeries(self, data: BalanceData, mode: Mode = Mode.ARRAY) -> np.ndarray | pd.DataFrame:
        """
        Рассчитывает временной ряд баланса
        
        :param mode:  [Mode.ARRAY, Mode.DF]  -  определяет  возвращаемое  значение;  если
            Mode.ARRAY, баланс возвращается в виде массива numpy, если Mode.DF, то в виде
            датафрейма pandas вместе со значениями времени
        :type mode: Mode
        ...
        :return: временной ряд баланса
        :rtype: np.ndarray | pd.DataFrame
        """
        # расчет сумм
        sums = self.calcSumSeries(data)
        diff_sums = self.calcSumsDiffSeries(sums)
        # расчет конвергенции
        convs = self.calcConvSeries(data)

        # расчет баланса
        balance = self.calcBalanceSeries(diff_sums, convs)

        if mode == Mode.ARRAY:
            return balance
        
        elif mode == Mode.DF:
            return self.makeBalanceDF(balance)
    
    def calcRegionBalance(self, region: Region, data: DataLoader) -> RegionBalance:
        """Рассчитывает баланс для данного региона"""
        # обрабатываем регион
        grid = data.getGrid()
        processor = RegionProcessor(region, grid)
        regdata = processor.getRegionData()

        balance_data = BalanceData(reg_data=regdata, data=data)
        balance = self.getBalanceSeries(balance_data)

        return RegionBalance(region, balance)
   
    def __call__(self, data: BalanceData, mode: Mode = Mode.ARRAY) -> np.ndarray | pd.DataFrame:
        self.getBalanceSeries(data, mode)
