from cal_cs import *

# environment settings
arcpy.env.workspace = r"C:\Users\hao9717\Documents\Esri\CellsizeRef\workspace"
arcpy.env.overwriteOutput = True

# Test case #1a: single raster(32145), env_ocs=54004
input_raster = arcpy.sa.Raster(r"C:\Users\hao9717\Documents\Esri\CellsizeRef\Data\landuser")
cs_new = single_raster_check(input_raster, env_ocs=arcpy.SpatialReference(3857))
print('The new cellsize is {}'.format(cs_new))

# Test case #1b: single raster(32145), env_ocs=54004, env_cs=100
input_raster = arcpy.sa.Raster(r"C:\Users\hao9717\Documents\Esri\CellsizeRef\Data\landuser")
cs_new = single_raster_check(input_raster, env_ocs=arcpy.SpatialReference(3857), env_cellsize=100)
print('The new cellsize is {}'.format(cs_new))

# Test case #1c: single raster(32145), env_ocs=26911, env_cs=raster(3380)
input_raster = arcpy.sa.Raster(r"C:\Users\hao9717\Documents\Esri\CellsizeRef\Data\landuser")
cellsize_raster = arcpy.sa.Raster(r"C:\Users\hao9717\Documents\Esri\CellsizeRef\Data\landuser_3338")
cs_new = single_raster_check(input_raster, env_ocs=arcpy.SpatialReference(26911), env_cellsize=cellsize_raster)
print('The new cellsize is {}'.format(cs_new))

# Test case #1d: single raster(32145), env_ocs=4269, env_cs=raster(3380)
input_raster = arcpy.sa.Raster(r"C:\Users\hao9717\Documents\Esri\CellsizeRef\Data\landuser")
cellsize_raster = arcpy.sa.Raster(r"C:\Users\hao9717\Documents\Esri\CellsizeRef\Data\landuser_3338")
cs_new = single_raster_check(input_raster, env_ocs=arcpy.SpatialReference(4269), env_cellsize=cellsize_raster)
print('The new cellsize is {}'.format(cs_new))

# Test case #2a: euclidean distance tool, feature, env_ocs=26911, env_cs=raster(3380)
input_feature = r"C:\Users\hao9717\Documents\Esri\QATest\py\pydata\v107\sa\global\shapefile\rec_sites.shp"
cellsize_raster = arcpy.sa.Raster(r"C:\Users\hao9717\Documents\Esri\CellsizeRef\Data\landuser_3338")
cs_new = euclidean_distance_check(input_feature, env_ocs=arcpy.SpatialReference(26911),
                                  env_cellsize=cellsize_raster)
print('The new cellsize for #2a is {}'.format(cs_new))

# print(calculate_resolution_preserving_cellsize(cellsize_raster,
#                                                output_spatial_reference=arcpy.SpatialReference(26911),
#                                                env_extent=cellsize_raster.extent))

# Test case #2b: euclidean distance tool, feature, env_ocs=26911
input_feature = r"C:\Users\hao9717\Documents\Esri\QATest\py\pydata\v107\sa\global\shapefile\rec_sites.shp"
cs_new = euclidean_distance_check(input_feature, env_ocs=arcpy.SpatialReference(26911))
print('The new cellsize for #2b is {}'.format(cs_new))

# Test case #2c: euclidean distance tool, feature, env_snapraster=raster(3380)
input_feature = r"C:\Users\hao9717\Documents\Esri\QATest\py\pydata\v107\sa\global\shapefile\rec_sites.shp"
snap_raster = arcpy.sa.Raster(r"C:\Users\hao9717\Documents\Esri\CellsizeRef\Data\landuser_3338")
cs_new = euclidean_distance_check(input_feature, env_snapraster=snap_raster)
print('The new cellsize for #2c is {}'.format(cs_new))
# print(calculate_resolution_preserving_cellsize(snap_raster, arcpy.Describe(input_feature).spatialReference,
#                                                snap_raster.extent))