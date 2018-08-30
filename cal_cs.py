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


def calculate_resolution_preserving_cellsize(input_ras, output_spatial_reference=None, env_extent=None):
    """
    Calculate resolution preserved cellsize when project raster to a different coordinate system
    :type input_ras: arcpy.sa.Raster
    :type output_spatial_reference: arcpy.SpatialReference
    :type env_extent: arcpy.Extent
    :rtype float
    """
    if not env_extent:
        env_extent = input_ras.extent
    sr = input_ras.spatialReference
    cs_x = input_ras.meanCellWidth
    cs_y = input_ras.meanCellHeight

    if not output_spatial_reference:
        return cs_x, cs_y

    pnt1 = arcpy.Point(env_extent.XMin, env_extent.YMin)
    pnt2 = arcpy.Point(env_extent.XMin, env_extent.YMax)
    pnt3 = arcpy.Point(env_extent.XMax, env_extent.YMax)
    pnt4 = arcpy.Point(env_extent.XMax, env_extent.YMin)

    array = arcpy.Array([pnt1, pnt2, pnt3, pnt4])

    polygon = arcpy.Polygon(array, sr)
    area_old = polygon.getArea("PLANAR", "SQUAREMETERS")
    # print(area_input)

    polygon_new = polygon.densify("DISTANCE", min(cs_x, cs_y), min(cs_x, cs_y))
    polygon_reproject = polygon_new.projectAs(output_spatial_reference)
    area_new = polygon_reproject.getArea("PLANAR", "SQUAREMETERS")
    # print(area_output)

    cs_new = math.sqrt((area_new / area_old) * cs_x * cs_y)
    return cs_new, cs_new


def single_raster_check(input_ras, env_ocs=None, env_cellsize=None, env_extent=None, env_snapraster=None):
    """
    Calculate correct cellsize with only one raster input, can be used to verify
    tools such as Abs, Lookup, Reclassify, Slice, etc.
    :type input_ras: arcpy.sa.Raster
    :type env_ocs: arcpy.SpatialReference
    :type env_cellsize: float or arcpy.sa.Raster
    :type env_extent: arcpy.Extent
    :type env_snapraster: arcpy.sa.Raster
    :rtype: float
    """
    # Calculate tool-specific extent if no specific analysis extent is specified
    if env_extent is None:
        env_extent = input_ras.extent

    # Cell size is specified implicitly
    if env_cellsize is None:
        if env_ocs is None:
            return input_ras.meanCellWidth, input_ras.meanCellHeight
        if env_snapraster is None:
            return calculate_resolution_preserving_cellsize(input_ras, env_ocs, env_extent)
        return calculate_resolution_preserving_cellsize(input_ras, env_ocs, env_snapraster.extent)

    # Cell size is specified explicitly
    if type(env_cellsize) == int or type(env_cellsize) == float:
        return env_cellsize, env_cellsize
    if env_ocs is None:
        return calculate_resolution_preserving_cellsize(env_cellsize, input_ras.spatialReference, env_cellsize.extent)
    return calculate_resolution_preserving_cellsize(env_cellsize, env_ocs, env_cellsize.extent)


def multi_raster_check(input_ras_list, env_ocs=None, env_cellsize=None, env_extent=None, env_snapraster=None):
    """
    Calculate correct cellsize with multiple raster inputs, can be used to verify
    tools such as Plus, Weighted Overlay, etc.
    :type input_ras_list: List[arcpy.sa.Raster]
    :type env_ocs: arcpy.SpatialReference
    :type env_cellsize: float or arcpy.sa.Raster
    :type env_extent: arcpy.Extent
    :type env_snapraster: arcpy.sa.Raster
    :rtype: float
    """
    # TODO
    # learn from Jim what extent to use when project cell size with multiple raster inputs


def euclidean_distance_check(param_input, param_cellsize=None, env_ocs=None, env_cellsize=None, env_extent=None,
                             env_snapraster=None):
    """
    Calculate correct cellsize with one raster or feature input and parameter cellsize, can be used to verify
    tools such as Euclidean Distance etc.
    :type param_input: arcpy.sa.Raster or String (feature input path)
    :type param_cellsize: float or arcpy.sa.Raster
    :type env_ocs: arcpy.SpatialReference
    :type env_cellsize: float or arcpy.sa.Raster
    :type env_extent: arcpy.Extent
    :type env_snapraster: arcpy.sa.Raster
    :rtype: float
    """
    if type(param_input) == arcpy.sa.Raster:
        input_spatialreference = param_input.spatialReference
        if env_extent is None:
            env_extent = param_input.extent
    else:
        input_spatialreference = arcpy.Describe(param_input).spatialReference
        if env_extent is None:
            env_extent = arcpy.Describe(param_input).extent

    if param_cellsize is None:
        # Environment cell size is specified implicitly
        if env_cellsize is None:
            if type(param_input) == arcpy.sa.Raster:
                if env_ocs is None:
                    return param_input.meanCellWidth, param_input.meanCellHeight
                if env_snapraster is None:
                    return calculate_resolution_preserving_cellsize(param_input, env_ocs, env_extent)
                return calculate_resolution_preserving_cellsize(param_input, env_ocs, env_snapraster.extent)
            # Input is a feature class
            if env_snapraster is None:
                # 250 rule here
                if env_ocs is None:
                    new_cellsize = min(env_extent.XMax - env_extent.XMin,
                                       env_extent.YMax - env_extent.YMin) / 250
                    return new_cellsize, new_cellsize
                # 250 rule applied to reprojected extent (project data or extent?)
                arcpy.Select_analysis(param_input, 'tmp.shp', '')
                arcpy.env.extent = env_extent
                arcpy.Project_management(param_input, 'tmp2.shp', env_ocs)
                feature_extent = arcpy.Describe('tmp2.shp').extent
                new_cellsize = min(feature_extent.XMax - feature_extent.XMin,
                                   feature_extent.YMax - feature_extent.YMin) / 250
                arcpy.env.extent = ""
                return new_cellsize, new_cellsize
            if env_ocs is None:
                return calculate_resolution_preserving_cellsize(env_snapraster, input_spatialreference,
                                                                env_snapraster.extent)
            return calculate_resolution_preserving_cellsize(env_snapraster, env_ocs, env_snapraster.extent)
        # Environment cell size is specified explicitly
        if type(env_cellsize) == int or type(env_cellsize) == float:
            return env_cellsize, env_cellsize
        if env_ocs is None:
            return calculate_resolution_preserving_cellsize(env_cellsize, input_spatialreference, env_cellsize.extent)
        return calculate_resolution_preserving_cellsize(env_cellsize, env_ocs, env_cellsize.extent)

    # Parameter cell size is specified explicitly
    if type(param_cellsize) == int or type(param_cellsize) == float:
        return param_cellsize, param_cellsize
    if env_ocs is None:
        return calculate_resolution_preserving_cellsize(param_cellsize, input_spatialreference, param_cellsize.extent)
    return calculate_resolution_preserving_cellsize(param_cellsize, env_ocs, param_cellsize.extent)


def main():
    # # Test case #1a: single raster(32145), env_ocs=54004
    # input_raster = arcpy.sa.Raster(r"C:\Users\hao9717\Documents\Esri\CellsizeRef\Data\landuser")
    # cs_new = single_raster_check(input_raster, env_ocs=arcpy.SpatialReference(3857))
    # print('The new cellsize is {}'.format(cs_new))
    #
    # # Test case #1b: single raster(32145), env_ocs=54004, env_cs=100
    # input_raster = arcpy.sa.Raster(r"C:\Users\hao9717\Documents\Esri\CellsizeRef\Data\landuser")
    # cs_new = single_raster_check(input_raster, env_ocs=arcpy.SpatialReference(3857), env_cellsize=100)
    # print('The new cellsize is {}'.format(cs_new))
    #
    # # Test case #1c: single raster(32145), env_ocs=26911, env_cs=raster(3380)
    # input_raster = arcpy.sa.Raster(r"C:\Users\hao9717\Documents\Esri\CellsizeRef\Data\landuser")
    # cellsize_raster = arcpy.sa.Raster(r"C:\Users\hao9717\Documents\Esri\CellsizeRef\Data\landuser_3338")
    # cs_new = single_raster_check(input_raster, env_ocs=arcpy.SpatialReference(26911), env_cellsize=cellsize_raster)
    # print('The new cellsize is {}'.format(cs_new))
    #
    # # Test case #1d: single raster(32145), env_ocs=4269, env_cs=raster(3380)
    # input_raster = arcpy.sa.Raster(r"C:\Users\hao9717\Documents\Esri\CellsizeRef\Data\landuser")
    # cellsize_raster = arcpy.sa.Raster(r"C:\Users\hao9717\Documents\Esri\CellsizeRef\Data\landuser_3338")
    # cs_new = single_raster_check(input_raster, env_ocs=arcpy.SpatialReference(4269), env_cellsize=cellsize_raster)
    # print('The new cellsize is {}'.format(cs_new))

    # Test case #2a: euclidean distance tool, feature, env_ocs=26911, env_cs=raster(3380)
    input_feature = r"C:\Users\hao9717\Documents\Esri\QATest\py\pydata\v107\sa\global\shapefile\rec_sites.shp"
    cellsize_raster = arcpy.sa.Raster(r"C:\Users\hao9717\Documents\Esri\CellsizeRef\Data\landuser_3338")
    cs_new = euclidean_distance_check(input_feature, env_ocs=arcpy.SpatialReference(26911),
                                      env_cellsize=cellsize_raster)
    print('The new cellsize for #2a is {}'.format(cs_new))
    # print(calculate_resolution_preserving_cellsize(cellsize_raster,
    #                                                output_spatial_reference=arcpy.SpatialReference(26911),
    #                                                env_extent=cellsize_raster.extent))

    # # Test case #2b: euclidean distance tool, feature, env_ocs=26911
    # input_feature = r"C:\Users\hao9717\Documents\Esri\QATest\py\pydata\v107\sa\global\shapefile\rec_sites.shp"
    # cs_new = euclidean_distance_check(input_feature, env_ocs=arcpy.SpatialReference(26911))
    # print('The new cellsize for #2b is {}'.format(cs_new))

    # # Test case #2c: euclidean distance tool, feature, env_snapraster=raster(3380)
    # input_feature = r"C:\Users\hao9717\Documents\Esri\QATest\py\pydata\v107\sa\global\shapefile\rec_sites.shp"
    # snap_raster = arcpy.sa.Raster(r"C:\Users\hao9717\Documents\Esri\CellsizeRef\Data\landuser_3338")
    # cs_new = euclidean_distance_check(input_feature, env_snapraster=snap_raster)
    # print('The new cellsize for #2c is {}'.format(cs_new))
    # print(calculate_resolution_preserving_cellsize(snap_raster, arcpy.Describe(input_feature).spatialReference,
    #                                                snap_raster.extent))


if __name__ == "__main__":
    main()
