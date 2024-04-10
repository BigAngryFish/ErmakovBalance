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
        self.transposed_shape = (
            self.original_shape[1],
            self.original_shape[0],
            self.original_shape[2],
        )

        self.region_id: Id = self.getDefaultRegionRange()
        self.original_dates: DateData = self.getDefaultDateRange()
    
    @property
    def timedim(self) -> int:
        """Возвращает количество единиц времени"""
        return self.original_dates.end_id - self.original_dates.start_id + 1
    
    def getGrid(self) -> Grid:
        """Возвращает сетку"""
        lat = np.array(self._db["lat"])
        lon = np.array(self._db["lon"])

        grid = Grid(lat=lat, lon=lon)
        return grid
    
    def getTargetMap(self, day_id: int) -> np.ndarray:
        data_map = self._db[self.target_name][..., day_id]
        return np.transpose(data_map)
    
    def getUMap(self, day_id: int) -> np.ndarray:
        return np.transpose(self._db["U"][..., day_id])
    
    def getVMap(self, day_id: int) -> np.ndarray:
        return np.transpose(self._db["V"][..., day_id])

    def getDefaultDateRange(self) -> DateData:
        """Вычисляет дефолтный временной диапазон"""
        start_id = 0
        end_id = self.original_shape[2] - 1

        start_day = self._stimeToDate(self._db[self.time_variable][start_id])
        end_day = self._stimeToDate(self._db[self.time_variable][end_id])

        next_day = self._stimeToDate(self._db[self.time_variable][start_id + 1])
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
