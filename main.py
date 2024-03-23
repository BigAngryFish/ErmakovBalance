import cv2 as cv

from regions import FieldMaker, Region

lon = 58.0, 70.0
lat = 58.0, 67.0

reg1 = Region(
    lat_min=59.0,
    lat_max=65.0,
    lon_min=59.75,
    lon_max=66.25,
)

if __name__ == "__main__":
    field_maker = FieldMaker(lat, lon)

    field_maker.addGrid()
    field_maker.addRegion(reg1)

    field = field_maker.getField()

    cv.imwrite("grid.jpg", field)
  
    # cv.namedWindow("Grid", cv.WINDOW_NORMAL) 
    # cv.resizeWindow("Grid", Field.image_size, Field.image_size) 
    # cv.imshow("Grid", field)
    
    # cv.waitKey(0)
    # cv.destroyAllWindows() 
    