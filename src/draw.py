import numpy as np
import cv2 as cv
from math import sqrt

from dataclasses import dataclass

from src.data_processing import Region

class Field():

    def __init__(self, region: Region) -> None:
        
        self.pixcel_step = 100
        self.grid_step = 1

        self.height: int
        self.width: int

        self.lat = region.down, region.up
        self.lon = region.left, region.right

        self.lat_steps = self.calcSteps(self.lat)
        self.lon_steps = self.calcSteps(self.lon)

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
                
    def getField(self) -> np.ndarray:
        return self.field

    def addGrid(self) -> np.ndarray:
        """Создает поле с сеткой и возвращает результат"""
        grid_drawer = GridDrawer(self)
        self.field = grid_drawer.drawGrid()
        return self.field
    
    def addRegion(self, region: Region, color: tuple = (255, 0, 0)) -> np.ndarray:
        """Добавление региона на поле"""
        drawer = RegionDrawer(self)
        self.field = drawer.draw(self.field, region, color)



class GridDrawer():

    def __init__(self, field: Field) -> None:
        """Инициализация"""

        self.field = field

        self.draw_grid_settings = (
            (0, 0, 0), # color
            1,         # thickness
        )

        self.label_settings = (
            cv.FONT_HERSHEY_SIMPLEX, # font
            1,                       # fontScale
            (0, 0, 0),               # color
            2,                       # thickness
            cv.LINE_AA
        )
    
    def drawGrid(self) -> np.ndarray:
        """Создает поле с сеткой и возвращает результат"""
        img = self.field.field
        img = self.drawLatLines(img, self.field.lat, self.field.lon)
        img = self.drawLonLines(img, self.field.lat, self.field.lon)
        return img
    
    def drawLatLines(self, img: np.ndarray, lat: tuple, lon: tuple) -> np.ndarray:
        """Чертит горизонтальные линии"""
        line_length = self.calcLineLength(lon)
        for step in range(self.field.lat_steps + 1):
            img = self.drawHorGrid(img, lat[0], step, line_length)
        
        return img

    def drawLonLines(self, img: np.ndarray, lat: tuple, lon: tuple) -> np.ndarray:
        """Чертит вертикальные линии"""
        line_length = self.calcLineLength(lat)
        for step in range(self.field.lon_steps + 1):
            img = self.drawVertGrid(img, lon[0], step, line_length)
        
        return img
     
    def drawVertGrid(self, img: np.ndarray, min_value: float, step: int, length) -> np.array:
        x = self.field.pixcel_step * (2 + step)
        y1 = self.field.pixcel_step
        y2 = y1 + length

        # draw line
        start_point = (x, y1)
        end_point = (x, y2)
        cv.line(img, start_point, end_point, *self.draw_grid_settings)

        # draw label
        vert_shift = 30
        hor_shift = 30
        coords = (x - hor_shift, y2 + vert_shift)
        lon_value = str(round(min_value + step * self.field.grid_step, 2))
        img = cv.putText(img, lon_value, coords, *self.label_settings)

        return img 

    def drawHorGrid(self, img: np.ndarray, min_value: float, step: int, length) -> np.array:
        y = self.field.height - self.field.pixcel_step * (2 + step)
        x1 = self.field.pixcel_step
        x2 = x1 + length

        # draw line
        start_point = (x1, y)
        end_point = (x2, y)
        cv.line(img, start_point, end_point, *self.draw_grid_settings)

        # draw label
        vert_shift = 30
        hor_shift = 0
        coords = (x2 + hor_shift, y + vert_shift)
        lon_value = str(round(min_value + step * self.field.grid_step, 2))
        img = cv.putText(img, lon_value, coords, *self.label_settings)

        return img 

    def calcLineLength(self, coords: tuple) -> int:
        """Возвращает длину горизонтальной линии"""
        steps = self.field.calcSteps(coords)
        length = (steps + 2) * self.field.pixcel_step
        return length


class RegionDrawer():

    def __init__(self, field: Field) -> None:
        "Инициализация"

        self.field = field

        self.color: tuple = (0, 0, 255)
        self.thickness: int = 2

    def latToPixcel(self, degree: float) -> int:
        step = (degree - self.field.lat[0]) / self.field.grid_step
        pixcel = int((step + 2) * self.field.pixcel_step)
        return pixcel
    
    def lonToPixcel(self, degree: float) -> int:
        step = (degree - self.field.lon[0]) / self.field.grid_step
        pixcel = int((step + 2) * self.field.pixcel_step)
        return pixcel

    def calcEdgePoints(self, region: Region) -> tuple:
        """
        Рассчитывает краевые точки региона
        
        :return: кортеж  с  краевыми точками региона вида  (start_point,  end_point), где
            start_point - точка левого верхнего угла, end_point  -  точка правого нижнего
            угла
        """
        start_x = int(self.lonToPixcel(region.left))
        end_x = int(self.lonToPixcel(region.right))
        start_y = self.field.height - int(self.latToPixcel(region.down))
        end_y = self.field.height - int(self.latToPixcel(region.up))

        return (start_x, start_y), (end_x, end_y)
        
    def draw(self, img: np.ndarray, region: Region, color: tuple = None) -> np.ndarray:
        """Отрисовывает регион и возвращает результат"""
        points = self.calcEdgePoints(region)

        if color == None: color = self.color
        img = cv.rectangle(img, *points, color, self.thickness)

        return img
