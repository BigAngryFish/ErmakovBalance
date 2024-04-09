import math

from containers import *
from constants import *


def verifyMap(data_map: np.ndarray) -> None:
    """"Проверяет размерность карты"""

    if not isinstance(data_map, np.ndarray):
        raise TypeError(f"expected numpy.ndarray for 'data_map")

    if data_map.ndim != 2:
        raise TypeError(f"expected 2D array for 'data_map'")

    if data_map.shape != MAP_SIZE:    
        raise ValueError(f"'data_map' must have shape of {MAP_SIZE}")


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
