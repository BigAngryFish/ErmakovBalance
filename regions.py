import numpy as np
import cv2 as cv

from dataclasses import dataclass

# class Area():

#     def __init__(self, number: int, height: int, width: int) -> None:
#         self.number = number

#         self.height = height
#         self.width = width

#         self.regions: list = []

#     def add_region(self, lat: int, lon: int) -> None:
#         pass

# AREAS = {
#     1 : {
#         1 : {"lag" : (59.0, 65.0), "lon" : (59.5, 66.0)},
#         2 : {"lag" : (59.0, 65.0), "lon" : (59.75, 66.25)},
#         3 : {"lag" : (59.0, 65.0), "lon" : (60.0, 66.5)},
#         4 : {"lag" : (59.0, 65.0), "lon" : (59.25, 65.75)},
#     }
# }


@dataclass
class Region:
    """Класс для хранения координат региона"""
    lat_min: float
    lat_max: float
    lon_max: float
    lon_min: float

    color: tuple = (0, 0, 255)
    thickness: int = 2


class FieldMaker():

    def __init__(self, lat: tuple, lon: tuple) -> None:
        
        self.pixcel_step = 100
        self.grid_step = 1

        self.height: int
        self.width: int

        self.draw_grid_settings = (
            (0, 0, 0), # color
            1,         # thickness
        )
        self.label_settings = (
            cv.FONT_HERSHEY_SIMPLEX, # font
            1,                       # fontScale
            (0, 0, 0),             # color
            2,                       # thickness
            cv.LINE_AA
        )

        self.lat = lat
        self.lon = lon

        self.lat_steps = self.calcSteps(lat)
        self.lon_steps = self.calcSteps(lon)

        self.field = self.createField()

    def createField(self) -> np.ndarray:
        """Инициализирует поле"""
        padding = 4
        self.height = (self.lat_steps + padding) * self.pixcel_step
        self.width = (self.lon_steps + padding) * self.pixcel_step
        self.field = np.zeros((self.height, self.width, 3)) + 255
        return self.field


    def calcSteps(self, coords: tuple) -> int:
        coord_min, coord_max = coords
        steps = int((coord_max - coord_min) / self.grid_step)
        return steps

    
    def calcLineLength(self, coords: tuple) -> int:
        """Возвращает длину горизонтальной линии"""
        steps = self.calcSteps(coords)
        length = (steps + 2) * self.pixcel_step
        return length
    
    def drawVertGrid(self, field: np.ndarray, min_value: float, step: int, length) -> np.array:
        x = self.pixcel_step * (2 + step)
        y1 = self.pixcel_step
        y2 = y1 + length

        # draw line
        start_point = (x, y1)
        end_point = (x, y2)
        cv.line(field, start_point, end_point, *self.draw_grid_settings)

        # draw label
        vert_shift = 30
        hor_shift = 30
        coords = (x - hor_shift, y2 + vert_shift)
        lon_value = str(round(min_value + step * self.grid_step, 2))
        field = cv.putText(field, lon_value, coords, *self.label_settings)

        return field 

    def drawHorGrid(self, field: np.ndarray, min_value: float, step: int, length) -> np.array:
        y = self.height - self.pixcel_step * (2 + step)
        x1 = self.pixcel_step
        x2 = x1 + length

        # draw line
        start_point = (x1, y)
        end_point = (x2, y)
        cv.line(field, start_point, end_point, *self.draw_grid_settings)

        # draw label
        vert_shift = 30
        hor_shift = 0
        coords = (x2 + hor_shift, y + vert_shift)
        lon_value = str(round(min_value + step * self.grid_step, 2))
        field = cv.putText(field, lon_value, coords, *self.label_settings)

        return field 
    
    def drawLonLines(self, field: np.ndarray, lat: tuple, lon: tuple) -> np.ndarray:
        """Чертит вертикальные линии"""
        line_length = self.calcLineLength(lat)
        for step in range(self.lon_steps + 1):
            field = self.drawVertGrid(field, lon[0], step, line_length)
        
        return field
        
    def drawLatLines(self, field: np.ndarray, lat: tuple, lon: tuple) -> np.ndarray:
        """Чертит горизонтальные линии"""
        line_length = self.calcLineLength(lon)
        for step in range(self.lat_steps + 1):
            field = self.drawHorGrid(field, lat[0], step, line_length)
        
        return field
            
    def getField(self) -> np.ndarray:
        return self.field

    def addGrid(self) -> np.ndarray:
        """Создает поле с сеткой и возвращает результат"""
        self.field = self.drawLatLines(self.field, self.lat, self.lon)
        self.field = self.drawLonLines(self.field, self.lat, self.lon)
        return self.field
    
    def latToPixcel(self, degree: float) -> int:
        step = (degree - self.lat[0]) / self.grid_step
        pixcel = int((step + 2) * self.pixcel_step)
        return pixcel
    
    def lonToPixcel(self, degree: float) -> int:
        step = (degree - self.lon[0]) / self.grid_step
        pixcel = int((step + 2) * self.pixcel_step)
        return pixcel

    def addRegion(self, region: Region) -> np.ndarray:
        """Добавление региона на поле"""
        start_x = int(self.lonToPixcel(region.lon_min))
        end_x = int(self.lonToPixcel(region.lon_max))
        start_y = self.height - int(self.latToPixcel(region.lat_min))
        end_y = self.height - int(self.latToPixcel(region.lat_max))

        start_point = start_x, start_y
        end_point = end_x, end_y

        settings = region.color, region.thickness
        self.field = cv.rectangle(self.field, start_point, end_point, *settings)
