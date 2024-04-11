# метров в одном градусе широты (по вертикали)
LAT_DEGREE_LENGTH_METERS = 111 * 1e3

# ячейки с шагом 0.25 градуса
COEF = 4
# длина стороны ячейки в градусах
CELL_STEP = 0.25

# длина широтной стороны ячейки
CELL_LENGTH_METERS = LAT_DEGREE_LENGTH_METERS / COEF

# расчет сетки
STD_WIDTH = 1440
STD_HEIGTH = 720    
OPT_IMAGE_TOP0 = True

MAP_SIZE = (STD_HEIGTH, STD_WIDTH)
