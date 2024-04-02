import numpy as np
import h5netcdf
import time

start_time = time.time()

STD_WIDTH = 1440
STD_HEIGTH = 720

OPT_IMAGE_TOP0 = True

STD_lons = [ (20.125 + X * 0.25) if X<640 else (20.125 + (X - 1440) * 0.25) for X in range(STD_WIDTH) ]
STD_lats_Btm0 = [ 89.875 - (719 - Y) * 0.25 for Y in range(STD_HEIGTH) ]
STD_lats_Top0 = [ (719 - Y) * 0.25 - 89.875 for Y in range(STD_HEIGTH) ]
STD_lats = STD_lats_Top0 if OPT_IMAGE_TOP0 else STD_lats_Btm0

lat_up = 55
lat_down = 45
lon_left = 128
lon_right = 135

closest = lambda num,collection:min(collection,key=lambda x:abs(x-num))

coor_down = closest(lat_down,STD_lats)
coor_up = closest(lat_up,STD_lats)
coor_right = closest(lon_right,STD_lons) + 0.25
coor_left = closest(lon_left,STD_lons) + 0.25

id_down = STD_lats.index(coor_down)
id_up = STD_lats.index(coor_up)
id_right = STD_lons.index(coor_right)
id_left = STD_lons.index(coor_left)

# Расчет длины границы с учетом широты
import math
area_lats = 111/4*10**3

area_up = 111/4*math.cos(math.radians(abs(coor_up)))*10**3
area_down = 111/4*math.cos(math.radians(abs(coor_down)))*10**3

def pwv(str):
    f1 = h5netcdf.File(str, "r")

    pwv_r = np.array([np.transpose(np.array(f1['PWV'][...,i]))[id_up:id_down+1,id_right] for i in range(f1['PWV'].shape[2])])
    pwv_d = np.array([np.transpose(np.array(f1['PWV'][...,i]))[id_down,id_left:id_right+1] for i in range(f1['PWV'].shape[2])])

    # Расчет матрицы площади с учетом широты
    area_s = []
    up = coor_up
    for _ in range(len(pwv_r[0])):
        row_areas = [area_lats*111/4*math.cos(math.radians(abs(up)))*10**3]*len(pwv_d[0])
        area_s.append(row_areas)
        up -= 0.25
    area_s = np.array(area_s)
    # ИВС по площади
    pwv_s = np.array(np.transpose(np.array(f1['PWV'][...,0]))[id_up:id_down+1,id_left:id_right+1])

    # ИВС с учетом площади
    mult_s = pwv_s * area_s

    return mult_s.sum()

path = "../PWV_flow_._2012_01_.nc"
pwv_sum = pwv(path)

end_time = time.time()

print("sum: {:e}".format(pwv_sum))
print(f"time: {round(end_time - start_time, 2)} s")
