# File name: sa_verify_utils.py
# Author: Hao Hu (h.hu@esri.com)
# Date created: 8/24/2018
# Date last modified: 9/4/2018
# Python Version: 3.6

import arcpy
import math


def extent_to_polygon(extent, input_spatial_reference=None):
    """
    Convert extent to arcpy.Polygon object
    :type extent: arcpy.Extent
    :type input_spatial_reference: arcpy.SpatialReference
    :rtype arcpy.Polygon
    """
    pnt1 = arcpy.Point(extent.XMin, extent.YMin)
    pnt2 = arcpy.Point(extent.XMin, extent.YMax)
    pnt3 = arcpy.Point(extent.XMax, extent.YMax)
    pnt4 = arcpy.Point(extent.XMax, extent.YMin)
    array = arcpy.Array([pnt1, pnt2, pnt3, pnt4])
    return arcpy.Polygon(array, input_spatial_reference)


def get_extent(input_data, output_spatial_reference=None):
    """
    Get extent of input data in output coordinate system
    :type input_data: arcpy.sa.Raster or String (path to feature data)
    :type output_spatial_reference: arcpy.SpatialReference
    :rtype arcpy.Extent
    """
    if type(input_data) == arcpy.sa.Raster:
        polygon = extent_to_polygon(input_data.extent, input_data.spatialReference)\
            .densify("DISTANCE", input_data.meanCellWidth, input_data.meanCellWidth)\
            .projectAs(output_spatial_reference)
        return polygon.extent
    arcpy.Project_management(input_data, 'tmp.shp', output_spatial_reference)
    extent = arcpy.Describe('tmp.shp').extent
    arcpy.Delete_management("tmp.shp")
    return extent


def calculate_output_extent_intersect(input_list, output_spatial_reference=None):
    """
    Given input from a list, calculate extent of input intersect in output coordinate system
    :type input_list: a list of input spatial data
    :type output_spatial_reference: arcpy.SpatialReference
    :rtype arcpy.Polygon
    """
    extent_list = [get_extent(i, output_spatial_reference) for i in input_list]
    return extent_to_polygon(arcpy.Extent(min(map(lambda x: x.XMax, extent_list)),
                                          max(map(lambda x: x.XMin, extent_list)),
                                          min(map(lambda x: x.YMax, extent_list)),
                                          max(map(lambda x: x.YMin, extent_list))), output_spatial_reference)


def calculate_output_extent_union(input_list, output_spatial_reference=None):
    """
    Given input from a list, calculate extent of input union in output coordinate system
    :type input_list: a list of input spatial data
    :type output_spatial_reference: arcpy.SpatialReference
    :rtype: arcpy.Polygon
    """
    extent_list = [get_extent(i, output_spatial_reference) for i in input_list]
    return extent_to_polygon(arcpy.Extent(max(map(lambda x: x.XMax, extent_list)),
                                          min(map(lambda x: x.XMin, extent_list)),
                                          max(map(lambda x: x.YMax, extent_list)),
                                          min(map(lambda x: x.YMin, extent_list))), output_spatial_reference)


def update_extent_with_cellsize_snapraster(polygon, cellsize, snapraster=None):
    """
    This function calculate the updated extent with cellsize and snapraster if provided
    :type polygon: arcpy.Polygon
    :type cellsize: float
    :type snapraster: arcpy.sa.Raster
    :rtype arcpy.Polygon
    """
    arcpy.CopyFeatures_management(polygon, "tmp.shp")
    arcpy.env.cellSize = cellsize
    if snapraster:
        arcpy.env.snapRaster = snapraster
    arcpy.PolygonToRaster_conversion("tmp.shp", "FID", "tmp.tif", "", "", cellsize)
    arcpy.gp.clearEnvironment("cellSize")
    arcpy.gp.clearEnvironment("snapRaster")
    extent_raster = arcpy.sa.Raster("tmp.tif")
    extent_polygon = extent_to_polygon(extent_raster.extent, extent_raster.spatialReference)
    arcpy.Delete_management("tmp.shp")
    arcpy.Delete_management("tmp.tif")
    return extent_polygon


def calculate_resolution_preserving_cellsize(input_ras, output_spatial_reference=None, extent=None):
    """
    Calculate resolution preserved cellsize when project raster to a different coordinate system
    :type input_ras: arcpy.sa.Raster
    :type output_spatial_reference: arcpy.SpatialReference
    :type extent: arcpy.Extent
    :rtype float
    """
    if not extent:
        extent = input_ras.extent
    sr = input_ras.spatialReference
    cs_x = input_ras.meanCellWidth
    cs_y = input_ras.meanCellHeight

    if not output_spatial_reference or sr == output_spatial_reference:
        return cs_x, cs_y

    polygon_old = extent_to_polygon(extent, sr)
    polygon_new = polygon_old.densify("DISTANCE", cs_x, cs_x).projectAs(output_spatial_reference)
    area_old = polygon_old.getArea("PLANAR", "SQUAREMETERS")
    area_new = polygon_new.getArea("PLANAR", "SQUAREMETERS")
    cs_new = math.sqrt((area_new / area_old) * cs_x * cs_y)
    return cs_new


def raster_check(input_ras_list, env_ocs=None, env_cellsize=None, env_extent=None, env_snapraster=None,
                 extent_type="intersect"):
    """
    Calculate correct cellsize with only one raster input, can be used to verify
    tools such as Abs, Lookup, Reclassify, Slice, etc.
    :type input_ras_list: List[arcpy.sa.Raster]
    :type env_ocs: arcpy.SpatialReference
    :type env_cellsize: float or arcpy.sa.Raster
    :type env_extent: arcpy.Extent or arcpy.sa.Raster or String (path to feature data)
    :type env_snapraster: arcpy.sa.Raster
    :type extent_type: String
    :rtype: float, arcpy.Polygon
    """

    # Determine the output spatial reference
    if env_ocs is None:
        env_ocs = input_ras_list[0].spatialReference

    # Get env_extent and calculate output_extent
    if env_extent is None:
        if len(input_ras_list) == 1:
            output_shape = extent_to_polygon(get_extent(input_ras_list[0], env_ocs), env_ocs)
        else:
            if extent_type == "union":
                output_shape = calculate_output_extent_union(input_ras_list, env_ocs)
            else:
                output_shape = calculate_output_extent_intersect(input_ras_list, env_ocs)
    else:
        # assuming user specified extent is in first input's spatial reference
        output_shape = extent_to_polygon(env_extent, input_ras_list[0].spatialReference).projectAs(env_ocs)

    # Calculate new cell size
    if env_cellsize is None:  # Cell size is specified implicitly
        if env_snapraster is None:
            if len(input_ras_list) == 1:
                cs_new = max(map(lambda x: calculate_resolution_preserving_cellsize(
                    x, env_ocs, input_ras_list[0].extent), input_ras_list))
            else:
                cs_new = max(map(lambda x: calculate_resolution_preserving_cellsize(
                    x, env_ocs, output_shape.projectAs(x.spatialReference).extent), input_ras_list))
        else:
            cs_new = max(map(lambda x: calculate_resolution_preserving_cellsize(x, env_ocs, env_snapraster.extent),
                             input_ras_list))
    else:  # Cell size is specified explicitly
        if type(env_cellsize) == int or type(env_cellsize) == float:
            cs_new = env_cellsize
        else:
            cs_new = calculate_resolution_preserving_cellsize(env_cellsize, env_ocs, env_cellsize.extent)

    # Calculate output boundary
    output_boundary = update_extent_with_cellsize_snapraster(output_shape, cs_new, env_snapraster)
    return cs_new, output_boundary


def feature_check(input_fc, param_cellsize=None, env_ocs=None, env_cellsize=None, env_extent=None, env_snapraster=None):
    """
    Calculate correct cellsize with only one raster input, can be used to verify
    tools such as Abs, Lookup, Reclassify, Slice, etc.
    :type input_fc: String (feature input path)
    :type param_cellsize: float or arcpy.sa.Raster
    :type env_ocs: arcpy.SpatialReference
    :type env_cellsize: float or arcpy.sa.Raster
    :type env_extent: arcpy.Extent or arcpy.sa.Raster or String (path to feature data)
    :type env_snapraster: arcpy.sa.Raster
    :rtype: float, arcpy.Polygon
    """

    # Determine the output spatial reference
    if env_ocs is None:
        env_ocs = arcpy.Describe(input_fc).spatialReference

    # Get env_extent and calculate output_extent
    if env_extent is None:
        env_extent = arcpy.Describe(input_fc).extent
    output_shape = extent_to_polygon(get_extent(input_fc, env_ocs), env_ocs)

    # Calculate new cell size
    if param_cellsize is None:  # Parameter cell size is specified implicitly
        if env_cellsize is None:  # Environment cell size is specified implicitly
            if env_snapraster is None:
                if env_ocs is None:
                    # 250 rule
                    cs_new = min(env_extent.XMax - env_extent.XMin, env_extent.YMax - env_extent.YMin) / 250
                else:
                    # 250 rule applied to reprojected extent (project data or extent?)
                    arcpy.env.extent = env_extent
                    arcpy.Select_analysis(input_fc, 'tmp.shp', '')
                    arcpy.Project_management(input_fc, 'tmp2.shp', env_ocs)
                    feature_extent = arcpy.Describe('tmp2.shp').extent
                    cs_new = min(feature_extent.XMax - feature_extent.XMin, feature_extent.YMax - feature_extent.YMin)\
                             / 250
                    arcpy.gp.clearEnvironment("extent")
            else:
                cs_new = calculate_resolution_preserving_cellsize(env_snapraster, env_ocs, env_snapraster.extent)
        else:  # Environment cell size is specified explicitly
            if type(env_cellsize) == int or type(env_cellsize) == float:
                cs_new = env_cellsize
            else:
                cs_new = calculate_resolution_preserving_cellsize(env_cellsize, env_ocs, env_cellsize.extent)
    else:  # Parameter cell size is specified explicitly
        if type(param_cellsize) == int or type(param_cellsize) == float:
            cs_new = param_cellsize
        else:
            cs_new = calculate_resolution_preserving_cellsize(param_cellsize, env_ocs, param_cellsize.extent)

    # Calculate output boundary
    output_boundary = update_extent_with_cellsize_snapraster(output_shape, cs_new, env_snapraster)
    return cs_new, output_boundary


def create_raster_check(output_extent, param_cellsize=None,  env_ocs=None, env_cellsize=None, env_extent=None, env_snapraster=None):
    """
    Calculate correct cellsize with only one raster input, can be used to verify
    tools such as Abs, Lookup, Reclassify, Slice, etc.
    :type input_ras: arcpy.sa.Raster
    :type env_ocs: arcpy.SpatialReference
    :type env_cellsize: float or arcpy.sa.Raster
    :type env_extent: arcpy.Extent or arcpy.sa.Raster or String (path to feature data)
    :type env_snapraster: arcpy.sa.Raster
    :rtype: cellsize_x, cellsize_y, output_extent: float, float, arcpy.Extent
    """


def zonalstat_check(input_ras, env_ocs=None, env_cellsize=None, env_extent=None, env_snapraster=None):
    """
    Calculate correct cellsize with only one raster input, can be used to verify
    tools such as Abs, Lookup, Reclassify, Slice, etc.
    :type input_ras: arcpy.sa.Raster
    :type env_ocs: arcpy.SpatialReference
    :type env_cellsize: float or arcpy.sa.Raster
    :type env_extent: arcpy.Extent or arcpy.sa.Raster or String (path to feature data)
    :type env_snapraster: arcpy.sa.Raster
    :rtype: cellsize_x, cellsize_y, output_extent: float, float, arcpy.Extent
    """


def euclidean_distance_check(param_input, param_cellsize=None, env_ocs=None, env_cellsize=None, env_extent=None,
                             env_snapraster=None):
    """
    Calculate correct cellsize with one raster or feature input and parameter cellsize, can be used to verify
    tools such as Euclidean Distance etc.
    :type param_input: arcpy.sa.Raster or String (feature input path)
    :type param_cellsize: float or arcpy.sa.Raster
    :type env_ocs: arcpy.SpatialReference
    :type env_cellsize: float or arcpy.sa.Raster
    :type env_extent: arcpy.Extent or arcpy.sa.Raster or String (path to feature data)
    :type env_snapraster: arcpy.sa.Raster
    :rtype: float, arcpy.Polygon
    """
    if type(param_input) == arcpy.sa.Raster:
        if param_cellsize:
            return raster_check([param_input], env_ocs, param_cellsize, env_extent, env_snapraster, "intersect")
        return raster_check([param_input], env_ocs, env_cellsize, env_extent, env_snapraster, "intersect")
    else:
        return feature_check(param_input, param_cellsize, env_ocs, env_cellsize, env_extent, env_snapraster)


def main():
    # environment settings
    arcpy.env.workspace = r"C:\Users\hao9717\Documents\Esri\CellsizeRef\workspace"
    arcpy.env.overwriteOutput = True

    # Local tests
    # Test case #1a: single raster(32145), env_ocs=3857
    input_raster = arcpy.sa.Raster(r"C:\Users\hao9717\Documents\Esri\CellsizeRef\Data\landuser")
    cs_new, output_boundary = raster_check([input_raster], env_ocs=arcpy.SpatialReference(3857))
    print('The new cellsize is {}'.format(cs_new))
    arcpy.CopyFeatures_management(output_boundary, "output2.shp")

    # Test case #2a: euclidean distance tool, feature, env_ocs=26911, env_cs=raster(3380)
    input_feature = r"C:\Users\hao9717\Documents\Esri\QATest\py\pydata\v107\sa\global\shapefile\rec_sites.shp"
    cellsize_raster = arcpy.sa.Raster(r"C:\Users\hao9717\Documents\Esri\CellsizeRef\Data\landuser_3338")
    cs_new, output_boundary = euclidean_distance_check(input_feature, env_ocs=arcpy.SpatialReference(26911),
                                      env_cellsize=cellsize_raster)
    print('The new cellsize for #2a is {}'.format(cs_new))


if __name__ == "__main__":
    main()
