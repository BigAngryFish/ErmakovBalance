import cv2 as cv

import areas
from draw import Field
from palette import MAIN_COLORS
from data_processing import Region


# field
FIELD = Region(
    left=58.0, right=70.0,
    down=58.0, up=67.0,
)


if __name__ == "__main__":
    field_maker = Field(FIELD)

    field_maker.addGrid()
    for number, region in enumerate(areas.AREA2):
        color = MAIN_COLORS[number%12]
        field_maker.addRegion(region, color)

    field = field_maker.getField()

    cv.imwrite("grid.jpg", field)

