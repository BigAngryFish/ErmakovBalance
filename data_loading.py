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
        return self.date_data.end_id - self.date_data.start_id + 1
    
    # def getRegionData(self) -> ConvData:
    #     """Извлекает необходимые данные из БД"""

    #     target: h5netcdf.Variable = self._db[self.target_name]
    #     target_arr = target[
    #         self.region_id.left : self.region_id.right + 1,
    #         self.region_id.up : self.region_id.down + 1,
    #         self.date_data.start_id : self.date_data.end_id,
    #     ]

    #     U: h5netcdf.Variable = self._db["U"]
    #     U_arr = U[
    #         self.region_id.left : self.region_id.right + 1,
    #         self.region_id.up : self.region_id.down + 1,
    #         self.date_data.start_id : self.date_data.end_id,
    #     ]

    #     V: h5netcdf.Variable = self._db["V"]
    #     V_arr = V[
    #         self.region_id.left : self.region_id.right + 1,
    #         self.region_id.up : self.region_id.down + 1,
    #         self.date_data.start_id : self.date_data.end_id,
    #     ]

    #     data = ConvData(target=target_arr, U=U_arr, V=V_arr)
    #     return data
    
    def getTargetMap(self, day_id: int) -> np.ndarray:
        data_map = self._db[self.target_name][..., day_id]
        return np.transpose(data_map)
    
    def getUMap(self, day_id: int) -> np.ndarray:
        return np.transpose(self._db["U"][..., day_id])
    
    def getVMap(self, day_id: int) -> np.ndarray:
        return np.transpose(self._db["V"][..., day_id])
    
    # def getRegionDayData(self, day_id: int) -> ConvDayData:
    #     """Извлекает необходимые данные из БД"""

    #     target: h5netcdf.Variable = self._db[self.target_name]
    #     target_arr = target[
    #         self.region_id.left : self.region_id.right + 1,
    #         self.region_id.up : self.region_id.down + 1,
    #         day_id,
    #     ]

    #     U: h5netcdf.Variable = self._db["U"]
    #     U_arr = U[
    #         self.region_id.left : self.region_id.right + 1,
    #         self.region_id.up : self.region_id.down + 1,
    #         day_id,
    #     ]

    #     V: h5netcdf.Variable = self._db["V"]
    #     V_arr = V[
    #         self.region_id.left : self.region_id.right + 1,
    #         self.region_id.up : self.region_id.down + 1,
    #         day_id,
    #     ]

    #     data = ConvDayData(target=target_arr, U=U_arr, V=V_arr)
    #     return data
    
    # def setRegionId(self, region_id: Id | None) -> None:
    #     self.region_id = region_id
    
    # def setDateRange(self, date_range: tuple[date, date]) -> None:
    #     pass

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
    
    # def dayonvData(day: date) -> ConvData:
    #     """Возвращает данные для определенного дня"""
    #     pass

    def getBorderConc(self, day_id: int, region_id: Id) -> ConvConc:
        """Возвращает граничные значения концентраций для региона"""
        right = self._db[self.target_name][
            region_id.right,
            region_id.up : region_id.down + 1,
            day_id,
        ]
        left = self._db[self.target_name][
            region_id.left,
            region_id.up : region_id.down + 1,
            day_id,
        ]
        down = self._db[self.target_name][
            region_id.left : region_id.right + 1,
            region_id.down,
            day_id,
        ]
        up = self._db[self.target_name][
            region_id.left : region_id.right + 1,
            region_id.up,
            day_id,
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
        right_flow = self._db["U"][
            region_id.right,
            region_id.up : region_id.down + 1,
            day_id,
        ]
        left_flow = self._db["U"][
            region_id.left,
            region_id.up : region_id.down + 1,
            day_id,
        ]
        # V по границам  (м / с)
        down_flow = self._db["V"][
            region_id.left : region_id.right + 1,
            region_id.down,
            day_id,
        ]
        up_flow = self._db["V"][
            region_id.left : region_id.right + 1,
            region_id.up,
            day_id,
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
