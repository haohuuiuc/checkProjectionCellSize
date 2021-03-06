# File name: sa_verify_utils.py
# Author: Hao Hu (h.hu@esri.com)
# Date created: 8/24/2018
# Date last modified: 9/11/2018
# Python Version: 3.6

import arcpy
import math


def extent_to_polygon(extent, input_spatial_reference=None, in_ras=None):
    """
    Convert extent to arcpy.Polygon object
    :type extent: arcpy.Extent
    :type input_spatial_reference: arcpy.SpatialReference
    :type in_ras: arcpy.sa.Raster
    :rtype arcpy.Polygon
    """
    if extent.spatialReference:
        input_spatial_reference = extent.spatialReference
    pnt1 = arcpy.Point(extent.XMin, extent.YMin)
    pnt2 = arcpy.Point(extent.XMin, extent.YMax)
    pnt3 = arcpy.Point(extent.XMax, extent.YMax)
    pnt4 = arcpy.Point(extent.XMax, extent.YMin)
    array = arcpy.Array([pnt1, pnt2, pnt3, pnt4])
    polygon = arcpy.Polygon(array, input_spatial_reference)
    if in_ras is not None:
        polygon = polygon.densify("DISTANCE", in_ras.meanCellWidth, in_ras.meanCellWidth)
    return polygon


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
    return extent_to_polygon(arcpy.Extent(XMin=max(map(lambda x: x.XMin, extent_list)),
                                          YMin=max(map(lambda x: x.YMin, extent_list)),
                                          XMax=min(map(lambda x: x.XMax, extent_list)),
                                          YMax=min(map(lambda x: x.YMax, extent_list))), output_spatial_reference)


def calculate_output_extent_union(input_list, output_spatial_reference=None):
    """
    Given input from a list, calculate extent of input union in output coordinate system
    :type input_list: a list of input spatial data
    :type output_spatial_reference: arcpy.SpatialReference
    :rtype: arcpy.Polygon
    """
    extent_list = [get_extent(i, output_spatial_reference) for i in input_list]
    return extent_to_polygon(arcpy.Extent(XMin=min(map(lambda x: x.XMin, extent_list)),
                                          YMin=min(map(lambda x: x.YMin, extent_list)),
                                          XMax=max(map(lambda x: x.XMax, extent_list)),
                                          YMax=max(map(lambda x: x.YMax, extent_list))), output_spatial_reference)


def calculate_new_cellsize(input_ras, output_spatial_reference, extent_shape):
    """
    Calculate resolution preserved cellsize when project raster to a different coordinate system
    :type input_ras: arcpy.sa.Raster
    :type output_spatial_reference: arcpy.SpatialReference
    :type extent_shape: arcpy.Polygon
    :rtype float
    """
    sr = input_ras.spatialReference
    cs_x = input_ras.meanCellWidth
    cs_y = input_ras.meanCellHeight

    if sr == output_spatial_reference:
        return cs_x

    if arcpy.env.cellSizeProjectionMethod == "PRESERVE_RESOLUTION":
        polygon_new = extent_shape.projectAs(output_spatial_reference)
        if extent_shape.spatialReference.type == 'Projected':
            if extent_shape.spatialReference.linearUnitCode == 9003:
                area_old = extent_shape.getArea("PLANAR", "SQUAREFEET")
            else:
                area_old = extent_shape.getArea("PLANAR", "SQUAREMETERS")
        else:
            area_old = extent_shape.getArea("PLANAR")
        if polygon_new.spatialReference.type == 'Projected':
            if polygon_new.spatialReference.linearUnitCode == 9003:
                area_new = polygon_new.getArea("PLANAR", "SQUAREFEET")
            else:
                area_new = polygon_new.getArea("PLANAR", "SQUAREMETERS")
        else:
            area_new = polygon_new.getArea("PLANAR")

        cs_new = math.sqrt((area_new / area_old) * cs_x * cs_x)

        # cs_new = math.sqrt((area_new / area_old) * cs_x * cs_y)
    elif arcpy.env.cellSizeProjectionMethod == "CENTER_OF_EXTENT":
        x, y = extent_shape.centroid.X, extent_shape.centroid.Y
        pnt = arcpy.PointGeometry(arcpy.Point(x, y), sr)
        pnt_n = arcpy.PointGeometry(arcpy.Point(x + cs_x, y), sr)
        pnt_s = arcpy.PointGeometry(arcpy.Point(x - cs_x, y), sr)
        pnt_w = arcpy.PointGeometry(arcpy.Point(x, y - cs_y), sr)
        pnt_e = arcpy.PointGeometry(arcpy.Point(x, y + cs_y), sr)
        pnt_proj = pnt.projectAs(output_spatial_reference)
        cs_new = sum(map(lambda x: x.projectAs(output_spatial_reference).distanceTo(pnt_proj),
                         [pnt_n, pnt_s, pnt_w, pnt_e])) / 4
    else:
        if sr.type != output_spatial_reference.type:
            extent = extent_shape.extent
            pnt_tl = arcpy.PointGeometry(arcpy.Point(extent.XMin, extent.YMax), sr)
            pnt_tr = arcpy.PointGeometry(arcpy.Point(extent.XMax, extent.YMax), sr)
            pnt_bl = arcpy.PointGeometry(arcpy.Point(extent.XMin, extent.YMin), sr)
            pnt_br = arcpy.PointGeometry(arcpy.Point(extent.XMax, extent.YMin), sr)
            pnt_tl_proj = pnt_tl.projectAs(output_spatial_reference)
            pnt_tr_proj = pnt_tr.projectAs(output_spatial_reference)
            pnt_bl_proj = pnt_bl.projectAs(output_spatial_reference)
            pnt_br_proj = pnt_br.projectAs(output_spatial_reference)
            d1 = pnt_tl_proj.distanceTo(pnt_tr_proj) / pnt_tl.distanceTo(pnt_tr)
            d2 = pnt_tl_proj.distanceTo(pnt_bl_proj) / pnt_tl.distanceTo(pnt_bl)
            d3 = pnt_tl_proj.distanceTo(pnt_br_proj) / pnt_tl.distanceTo(pnt_br)
            d4 = pnt_bl_proj.distanceTo(pnt_br_proj) / pnt_bl.distanceTo(pnt_br)
            d5 = pnt_bl_proj.distanceTo(pnt_tr_proj) / pnt_bl.distanceTo(pnt_tr)
            d6 = pnt_tr_proj.distanceTo(pnt_br_proj) / pnt_tr.distanceTo(pnt_br)
            cs_new = cs_x * (d1 + d2 + d3 + d4 + d5 + d6) / 6
        else:
            if sr.linearUnitName == 'Meter' and output_spatial_reference.linearUnitName in ['Foot', 'Foot_US']:
                cs_new = cs_x * 3.28084
            elif sr.linearUnitName in ['Foot', 'Foot_US'] and output_spatial_reference.linearUnitName == 'Meter':
                cs_new = cs_x / 3.28084
            else:
                cs_new = cs_x
    return cs_new


def raster_check(input_ras_list, env_ocs=None, env_cellsize=None, env_extent=None, env_snapraster=None):
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

    # When input_ras_list is empty
    if len(input_ras_list) == 0:
        if env_ocs is None:
            aprx = arcpy.mp.ArcGISProject("CURRENT")
            sr = aprx.listMaps()[0].defaultCamera.getExtent().spatialReference
        else:
            sr = env_ocs
        if type(env_cellsize) == int or type(env_cellsize) == float:
            cs_new = env_cellsize
        else:
            if env_cellsize is None:
                cs_new = calculate_new_cellsize(env_snapraster, sr, extent_to_polygon(env_snapraster.extent,
                                                                                    in_ras=env_snapraster))
            else:
                cs_new = calculate_new_cellsize(env_cellsize, sr,
                            extent_to_polygon(env_cellsize.extent, in_ras=env_cellsize))
        return cs_new, extent_to_polygon(env_extent).projectAs(sr)

    # Determine the output spatial reference
    if env_ocs is None:
        env_ocs = input_ras_list[0].spatialReference

    # Get env_extent and calculate output_extent
    if env_extent == "MAXOF":
        output_shape = calculate_output_extent_union(input_ras_list, env_ocs)
    elif env_extent == "MINOF":
        output_shape = calculate_output_extent_intersect(input_ras_list, env_ocs)
    else:
        output_shape = extent_to_polygon(env_extent.projectAs(env_ocs))

    # Calculate new cell size
    if env_cellsize is None or (type(env_cellsize) == str and env_cellsize == "MAXOF"):  # Cell size is specified implicitly
        if env_snapraster is None:
            if len(input_ras_list) == 1:
                cs_new = max(map(lambda x: calculate_new_cellsize(x, env_ocs,
                        extent_to_polygon(input_ras_list[0].extent, in_ras=input_ras_list[0])), input_ras_list))
            else:
                cs_new = max(map(lambda x: calculate_new_cellsize(
                    x, env_ocs, output_shape.projectAs(x.spatialReference)), input_ras_list))
        else:
            cs_new = max(map(lambda x: calculate_new_cellsize(x, env_ocs, extent_to_polygon(env_snapraster.extent,
                                                                in_ras=env_snapraster).projectAs(x.spatialReference)),
                             input_ras_list))
    elif type(env_cellsize) == str and env_cellsize == "MINOF":  # Cell size is specified implicitly
        if env_snapraster is None:
            if len(input_ras_list) == 1:
                cs_new = min(map(lambda x: calculate_new_cellsize(x, env_ocs,
                        extent_to_polygon(input_ras_list[0].extent, in_ras=input_ras_list[0])), input_ras_list))
            else:
                cs_new = min(map(lambda x: calculate_new_cellsize(
                    x, env_ocs, output_shape.projectAs(x.spatialReference)), input_ras_list))
        else:
            cs_new = min(map(lambda x: calculate_new_cellsize(x, env_ocs,
                        extent_to_polygon(env_snapraster.extent, in_ras=env_snapraster).projectAs(x.spatialReference)),
                        input_ras_list))
    else:  # Cell size is specified explicitly
        if type(env_cellsize) == int or type(env_cellsize) == float or type(env_cellsize) == str and \
                env_cellsize.replace('.', '', 1).isdigit():
            cs_new = env_cellsize
        else:
            cs_new = calculate_new_cellsize(env_cellsize, env_ocs,
                        extent_to_polygon(env_cellsize.extent, in_ras=env_cellsize))

    return cs_new, output_shape


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

    output_shape = extent_to_polygon(get_extent(input_fc, output_spatial_reference=env_ocs))
    # Calculate new cell size
    if param_cellsize is None:  # Parameter cell size is specified implicitly
        if env_cellsize is None:  # Environment cell size is specified implicitly
            if env_snapraster is None:
                if env_ocs is None:
                    # 250 rule
                    cs_new = min(env_extent.XMax - env_extent.XMin, env_extent.YMax - env_extent.YMin) / 250
                else:
                    # 250 rule applied to reprojected extent (project data or extent?)
                    feature_extent = env_extent.projectAs(env_ocs)
                    cs_new = min(feature_extent.XMax - feature_extent.XMin, feature_extent.YMax - feature_extent.YMin)\
                             / 250
            else:
                cs_new = calculate_new_cellsize(env_snapraster, env_ocs,
                            extent_to_polygon(env_snapraster.extent, in_ras=env_snapraster))
        else:  # Environment cell size is specified explicitly
            if type(env_cellsize) == int or type(env_cellsize) == float:
                cs_new = env_cellsize
            else:
                cs_new = calculate_new_cellsize(env_cellsize, env_ocs,
                            extent_to_polygon(env_cellsize.extent, in_ras=env_cellsize))
    else:  # Parameter cell size is specified explicitly
        if type(param_cellsize) == int or type(param_cellsize) == float:
            cs_new = param_cellsize
        else:
            cs_new = calculate_new_cellsize(param_cellsize, env_ocs,
                        extent_to_polygon(param_cellsize.extent, in_ras=param_cellsize))

    return cs_new, output_shape


def main():
    # Write test cases here

if __name__ == "__main__":
     main()