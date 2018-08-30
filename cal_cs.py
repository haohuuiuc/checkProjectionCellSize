# File name: cal_cs.py
# Author: Hao Hu (h.hu@esri.com)
# Date created: 8/24/2018
# Date last modified: 8/29/2018
# Python Version: 3.6

import arcpy
import math

# environment settings
arcpy.env.workspace = r"C:\Users\hao9717\Documents\Esri\CellsizeRef\workspace"
arcpy.env.overwriteOutput = True


def calculate_resolution_preserving_cellsize(input_ras, output_spatial_reference=None, analysis_extent=None):
    """
    Calculate resolution preserved cellsize when project raster to a different coordinate system
    :type input_ras: arcpy.sa.Raster
    :type output_spatial_reference: arcpy.SpatialReference
    :type analysis_extent: arcpy.Extent
    :rtype float
    """
    if not analysis_extent:
        analysis_extent = input_ras.extent
    sr = input_ras.spatialReference
    cs_x = input_ras.meanCellWidth
    cs_y = input_ras.meanCellHeight

    if not output_spatial_reference:
        return cs_x

    pnt1 = arcpy.Point(analysis_extent.XMin, analysis_extent.YMin)
    pnt2 = arcpy.Point(analysis_extent.XMin, analysis_extent.YMax)
    pnt3 = arcpy.Point(analysis_extent.XMax, analysis_extent.YMax)
    pnt4 = arcpy.Point(analysis_extent.XMax, analysis_extent.YMin)

    array = arcpy.Array([pnt1, pnt2, pnt3, pnt4])

    polygon = arcpy.Polygon(array, sr)
    area_input = polygon.getArea("PLANAR", "SQUAREMETERS")
    # print(area_input)

    polygon_new = polygon.densify("DISTANCE", min(cs_x, cs_y), min(cs_x, cs_y))
    polygon_reproject = polygon_new.projectAs(output_spatial_reference)
    area_output = polygon_reproject.getArea("PLANAR", "SQUAREMETERS")
    # print(area_output)

    cs_new = math.sqrt((area_output / area_input) * cs_x * cs_y)
    return cs_new


def single_raster_check(input_ras, env_ocs=None, env_cellsize=None, analysis_extent=None):
    """
    Calculate correct cellsize with only one raster input, can be used to verify
    tools such as Abs, Lookup, Reclassify, Slice, etc.
    :type input_ras: arcpy.sa.Raster
    :type env_ocs: arcpy.SpatialReference
    :type env_cellsize: float or arcpy.sa.Raster
    :rtype: float
    """

    if env_cellsize is None:
        return calculate_resolution_preserving_cellsize(input_ras, env_ocs, analysis_extent)
    if type(env_cellsize) == int or type(env_cellsize) == float:
        return env_cellsize
    if not env_ocs:
        return calculate_resolution_preserving_cellsize(env_cellsize, input_ras.spatialReference)
    return calculate_resolution_preserving_cellsize(env_cellsize, env_ocs)


def multi_raster_check(input_ras_list, env_ocs=None, env_cellsize=None):
    """
    Calculate correct cellsize with multiple raster inputs, can be used to verify
    tools such as Plus, Weighted Overlay, etc.
    :type input_ras_list: List[arcpy.sa.Raster]
    :type env_ocs: arcpy.SpatialReference
    :type env_cellsize: float or arcpy.sa.Raster
    :rtype: float
    """
    if env_cellsize is None:
        return max(map(lambda x: single_raster_check(x, env_ocs), input_ras_list))
    if type(env_cellsize) == int or type(env_cellsize) == float:
        return env_cellsize
    if not env_ocs:
        return calculate_resolution_preserving_cellsize(env_cellsize, input_ras_list[0].spatialReference)
    return calculate_resolution_preserving_cellsize(env_cellsize, env_ocs)

def single_input_with_cellsize_check(input_source, param_cellsize=None, env_ocs=None, env_snapraster=None,
                                   env_cellsize=None):
    """
    Calculate correct cellsize with one raster or feature input and parameter cellsize, can be used to verify
    tools such as Euclidean Distance etc.
    :type input_source: arcpy.sa.Raster or
    :type param_cellsize: float or arcpy.sa.Raster
    :type env_ocs: arcpy.SpatialReference
    :type env_snapraster: arcpy.sa.Raster
    :type env_cellsize: float or arcpy.sa.Raster
    :rtype: float
    """



def main():
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

    # Test case #2a: two rasters(32145, 3338), env_ocs=3857
    input_raster1 = arcpy.sa.Raster(r"C:\Users\hao9717\Documents\Esri\CellsizeRef\Data\landuser")
    input_raster2 = arcpy.sa.Raster(r"C:\Users\hao9717\Documents\Esri\CellsizeRef\Data\landuser_3338")
    cs_new = multi_raster_check([input_raster1, input_raster2], env_ocs=arcpy.SpatialReference(3857))
    print('The new cellsize is {}'.format(cs_new))

    # Test case #2a: two rasters(4269,32145), env_cs=raster(3338)
    input_raster1 = arcpy.sa.Raster(r"C:\Users\hao9717\Documents\Esri\CellsizeRef\Data\landuser_gcs")
    input_raster2 = arcpy.sa.Raster(r"C:\Users\hao9717\Documents\Esri\CellsizeRef\Data\landuser")
    cellsize_raster = arcpy.sa.Raster(r"C:\Users\hao9717\Documents\Esri\CellsizeRef\Data\landuser_3338")
    cs_new = multi_raster_check([input_raster1, input_raster2], env_cellsize=cellsize_raster)
    print('The new cellsize is {}'.format(cs_new))


if __name__ == "__main__":
    main()
