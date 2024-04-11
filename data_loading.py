import numpy as np
import h5netcdf
from datetime import date, datetime

from containers import *


class DataLoader():
    """Класс для загрузки данных"""

    def __init__(self, path: str, target_name: str) -> None:
        """Инициализация"""

        self._db: h5netcdf.File = h5netcdf.File(path, "r")
        self.target_name: str = target_name

        self.time_variable = "stime"

        self.original_shape = self._db[target_name].shape
        # self.transposed_shape = (
        #     self.original_shape[1],
        #     self.original_shape[0],
        #     self.original_shape[2],
        # )

        self._verifyData()

        self._seconds_step = self.getSecondsStep()
        self.region_id: Id = self.getDefaultRegionRange()
        self.default_date_range: DateRange = self.getDefaultDateRange()
        self._date_range: DateRange = self.default_date_range
    
    # @property
    # def timedim(self) -> int:
    #     """Возвращает количество единиц времени"""
    #     return self.date_range.end_id - self.date_range.start_id + 1

    def _verifyData(self) -> None:
        """Проверяет полученные данные"""
        self._verifyTime()

    def _verifyTime(self) -> None:
        """Проверяет временную переменную"""
        time_shape = self._db[self.time_variable].shape

        if len(time_shape) != 1:
            raise ValueError("Time variable is not 1-dimensional")
        
        if time_shape[0] <= 1:
            raise ValueError("Time variable contains only one value")
    
    @property
    def date_range(self) -> DateRange:
        """Возвращает временной диапазон"""
        return self._date_range
    
    @property
    def seconds_step(self) -> int:
        """Возвращает величину временного шага в секундах"""
        return self._seconds_step

    def getGrid(self) -> Grid:
        """Возвращает сетку"""
        lat = np.array(self._db["lat"])
        lon = np.array(self._db["lon"])

        grid = Grid(lat=lat, lon=lon)
        return grid
    
    def getDateRange(self) -> DateRange:
        return self.date_range
    
    def getTargetMap(self, day_id: int) -> np.ndarray:
        data_map = self._db[self.target_name][..., day_id]
        return np.transpose(data_map)
    
    def getUMap(self, day_id: int) -> np.ndarray:
        return np.transpose(self._db["U"][..., day_id])
    
    def getVMap(self, day_id: int) -> np.ndarray:
        return np.transpose(self._db["V"][..., day_id])
    
    def getSecondsStep(self) -> int:
        """Рассчитывает шаг времени в секундах"""
        first_day = self._stimeToDate(self._db[self.time_variable][0])
        second_day = self._stimeToDate(self._db[self.time_variable][1])
        _seconds_step = (second_day - first_day).total_seconds()
        return int(_seconds_step)

    def getDefaultDateRange(self) -> DateRange:
        """Вычисляет дефолтный временной диапазон"""
        start_id = 0
        end_id = self.original_shape[2] - 1

        start_day = self._stimeToDate(self._db[self.time_variable][start_id])
        end_day = self._stimeToDate(self._db[self.time_variable][end_id])

        date_data = DateRange(
            start=start_day, end=end_day,
            start_id=start_id, end_id=end_id,
            seconds=self.seconds_step,
        )

        return date_data
    
    def getTimeId(self, daytime: datetime) -> int:
        """Находит индекс ближайшего времени"""
        # список времен в оригинальном формате
        original_daytimes = list(self._db[self.time_variable])

        # тот же список времен в формате datetime
        daytimes = list(map(self._stimeToDate, original_daytimes))

        # массив с модулем разниц времен от переданного времени, в секундах
        iter_seconds_diffs = map(lambda x: (daytime - x).total_seconds(), daytimes)
        seconds_diff = np.abs(np.fromiter(iter_seconds_diffs, dtype=np.int32))

        # находим индекс минимального значения - это и есть индекс ближайшей даты
        min_id = int(np.argmin(seconds_diff))

        return min_id
    
    def setDateRange(self, start_day: datetime, end_day: datetime) -> None:
        """Задает временной диапазон"""
        start_id = self.getTimeId(start_day)
        end_id = self.getTimeId(end_day)

        correct_start_day = self.getDatetimeById(start_id)
        correct_end_day = self.getDatetimeById(end_id)

        self._date_range = DateRange(
            start_id=start_id,
            end_id=end_id,
            start=correct_start_day,
            end=correct_end_day,
            seconds=self.seconds_step,
        )

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
    
    def getDatetimeById(self, time_id: int) -> datetime:
        """
        Возвращает дату и время, соответствующие индексу 'time_id'
        """
        stime = self._db[self.time_variable][time_id]
        date_time = self._stimeToDate(stime)
        return date_time

    def getBorderConc(self, day_id: int, region_id: Id) -> ConvConc:
        """Возвращает граничные значения концентраций для региона"""
        conc_map = self._db[self.target_name][..., day_id]

        right = conc_map[
            region_id.right,
            region_id.up : region_id.down + 1,
        ]
        left = conc_map[
            region_id.left,
            region_id.up : region_id.down + 1,
        ]
        down = conc_map[
            region_id.left : region_id.right + 1,
            region_id.down,
        ]
        up = conc_map[
            region_id.left : region_id.right + 1,
            region_id.up,
        ]

        conc = ConvConc(
            right=right,
            left=left,
            down=down,
            up=up,
        )

        return conc
    
    def getBorderFlow(self, day_id: int, region_id: Id) -> ConvFlow:
        # U по границам (м / с)
        umap = self._db["U"][..., day_id]
        right_flow = umap[
            region_id.right,
            region_id.up : region_id.down + 1,
        ]
        left_flow = umap[
            region_id.left,
            region_id.up : region_id.down + 1,
        ]

        # V по границам  (м / с)
        vmap = self._db["V"][..., day_id]
        down_flow = vmap[
            region_id.left : region_id.right + 1,
            region_id.down,
        ]
        up_flow = vmap[
            region_id.left : region_id.right + 1,
            region_id.up,
        ]

        flow = ConvFlow(
            right=right_flow,
            left=left_flow,
            down=down_flow,
            up=up_flow,
        )

        return flow
    
    def getConvData(self, day_id: int, region_id: Id) -> ConvOriginalDayData:
        """
        Возвращает сырые данные необходимые для расчета конвергенции одного дня
        """
        conc = self.getBorderConc(day_id, region_id)
        flow = self.getBorderFlow(day_id, region_id)

        convdata = ConvOriginalDayData(conc=conc, flow=flow)
        return convdata
    
    def close(self) -> None:
        """Закрытие базы данных"""
        self._db.close()
