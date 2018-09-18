# File name: CellsizeExtentVerify.pyt
# Author: Hao Hu (h.hu@esri.com)
# Date created: 8/24/2018
# Date last modified: 9/11/2018
# Python Version: 3.6

from sa_verify_utils import *


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "CellsizeExtentVerify"
        self.alias = ""

        # allow overwrite tmp file
        arcpy.env.overwriteOutput = True

        # List of tool classes associated with this toolbox
        self.tools = [AbsVerify, PlusVerify, EucDistanceVerify, FocalStatVerify, FlowDirVerify, HillshadeVerify,
                      ExtractByRectVerify, IDWVerify, Point2RasterVerify, PointStatVerify, KernelDensityVerify,
                      CellStatVerify, CreateConstRasterVerify, ZonalStatVerify]


class AbsVerify(object):
    def __init__(self):
        self.label = "Abs"
        self.description = "Verify cellsize and extent for Abs tool"
        self.canRunInBackground = True

    def getParameterInfo(self):
        param0 = arcpy.Parameter(
            displayName="Input raster",
            name="in_ras",
            datatype=["DERasterDataset", "GPRasterLayer"],
            parameterType="Required",
            direction="Input")
        param1 = arcpy.Parameter(
            displayName="Environment Cell Size",
            name="env_cs",
            datatype=["DERasterDataset", "GPRasterLayer", "GPDouble", "GPString"],
            parameterType="Required",
            direction="Input")
        param1.value = "MAXOF"
        param2 = arcpy.Parameter(
            displayName="Output Boundary",
            name="out_features",
            datatype="GPFeatureLayer",
            parameterType="Optional",
            direction="Output")
        param3 = arcpy.Parameter(
            displayName="Output Generate by Actual Tool",
            name="in_ras_actual",
            datatype=["DERasterDataset", "GPRasterLayer"],
            parameterType="Optional",
            direction="Input")
        return [param0, param1, param2, param3]

    def execute(self, parameters, messages):
        arcpy.env.overwriteOutput = True
        in_ras = arcpy.sa.Raster(parameters[0].valueAsText)
        arcpy.AddMessage("Calculating")
        # get env cellsize
        if not parameters[1].valueAsText.replace('.', '', 1).isdigit() and parameters[1].valueAsText != "MINOF" and \
                parameters[1].valueAsText != "MAXOF":
            env_cs = arcpy.sa.Raster(parameters[1].valueAsText)
        else:
            env_cs = parameters[1].value
        # get env snapraster
        if arcpy.env.snapRaster:
            env_snap = arcpy.sa.Raster(arcpy.env.snapRaster)
        else:
            env_snap = None
        # get env extent
        env_extent = arcpy.env.extent or "MINOF"

        cs_new, output_boundary = raster_check([in_ras], env_ocs=arcpy.env.outputCoordinateSystem,
                                               env_cellsize=env_cs, env_extent=env_extent,
                                               env_snapraster=env_snap)
        arcpy.AddMessage("The expected raster cell size is {}".format(cs_new))
        if parameters[2].valueAsText is not None:
            arcpy.AddMessage("The extent of output raster (in polygon) has been added to the map.")
            arcpy.CopyFeatures_management(output_boundary, parameters[2].valueAsText)
        if parameters[3].valueAsText is not None:
            actual_ras = arcpy.sa.Raster(parameters[3].valueAsText)
            arcpy.AddMessage("The tool output raster cell size is {}".format(actual_ras.meanCellWidth))


class PlusVerify(object):
    def __init__(self):
        self.label = "Plus"
        self.description = "Verify cellsize and extent for Plus tool"
        self.canRunInBackground = True

    def getParameterInfo(self):
        param0 = arcpy.Parameter(
            displayName="Input raster or constant value 1",
            name="in_ras1",
            datatype=["DERasterDataset", "GPRasterLayer", "GPDouble"],
            parameterType="Required",
            direction="Input")
        param1 = arcpy.Parameter(
            displayName="Input raster or constant value 2",
            name="in_ras2",
            datatype=["DERasterDataset", "GPRasterLayer", "GPDouble"],
            parameterType="Required",
            direction="Input")
        param2 = arcpy.Parameter(
            displayName="Environment Cell Size",
            name="env_cs",
            datatype=["DERasterDataset", "GPRasterLayer","GPString", "GPDouble"],
            parameterType="Required",
            direction="Input")
        param2.value = "MAXOF"
        param3 = arcpy.Parameter(
            displayName="Output Boundary",
            name="out_features",
            datatype="GPFeatureLayer",
            parameterType="Optional",
            direction="Output")
        param4 = arcpy.Parameter(
            displayName="Output Generate by Actual Tool",
            name="in_ras_actual",
            datatype=["DERasterDataset", "GPRasterLayer"],
            parameterType="Optional",
            direction="Input")
        return [param0, param1, param2, param3, param4]

    def execute(self, parameters, messages):
        in_ras_list = []
        if type(parameters[0].value) != float:
            in_ras_list.append(arcpy.sa.Raster(parameters[0].valueAsText))
        if type(parameters[1].value) != float:
            in_ras_list.append(arcpy.sa.Raster(parameters[1].valueAsText))

        arcpy.AddMessage("Calculating")

        if len(in_ras_list) == 0 and (parameters[2].value == "MAXOF" or parameters[2].value == "MINOF"
                                      or type(arcpy.env.extent) != arcpy.Extent):
            arcpy.AddError("Cell size and extent must be specified if both inputs are numeric values.")
        else:
            # get env cellsize
            if not parameters[2].valueAsText.replace('.', '', 1).isdigit() and parameters[2].valueAsText != "MINOF" and \
                    parameters[2].valueAsText != "MAXOF":
                env_cs = arcpy.sa.Raster(parameters[2].valueAsText)
            else:
                env_cs = parameters[2].value
            # get env snapraster
            if arcpy.env.snapRaster:
                env_snap = arcpy.sa.Raster(arcpy.env.snapRaster)
            else:
                env_snap = None
            # get env extent
            env_extent = arcpy.env.extent or "MINOF"
            cs_new, output_boundary = raster_check(in_ras_list, env_ocs=arcpy.env.outputCoordinateSystem,
                                               env_cellsize=env_cs, env_extent=env_extent, env_snapraster=env_snap)
            arcpy.AddMessage("The expected raster cell size is {}".format(cs_new))
            if parameters[3].valueAsText is not None:
                arcpy.AddMessage("The extent of output raster (in polygon) has been added to the map.")
                arcpy.CopyFeatures_management(output_boundary, parameters[3].valueAsText)
            if parameters[4].valueAsText is not None:
                actual_ras = arcpy.sa.Raster(parameters[4].valueAsText)
                arcpy.AddMessage("The tool output raster cell size is {}".format(actual_ras.meanCellWidth))


class EucDistanceVerify(object):
    def __init__(self):
        self.label = "Euclidean Distance"
        self.description = "Verify cellsize and extent for EucDistance tool"
        self.canRunInBackground = True

    def getParameterInfo(self):
        param0 = arcpy.Parameter(
            displayName="Input Source",
            name="in_data",
            datatype=["DERasterDataset", "DEFeatureClass", "GPFeatureLayer", "GPRasterLayer"],
            parameterType="Required",
            direction="Input")
        param1 = arcpy.Parameter(
            displayName="Output cell size",
            name="param_cs",
            datatype=["DERasterDataset", "GPRasterLayer", "GPDouble"],
            parameterType="Optional",
            direction="Input")
        param2 = arcpy.Parameter(
            displayName="Environment Cell Size",
            name="env_cs",
            datatype=["DERasterDataset", "GPRasterLayer", "GPDouble", "GPString"],
            parameterType="Required",
            direction="Input")
        param2.value = "MAXOF"
        param3 = arcpy.Parameter(
            displayName="Output Boundary",
            name="out_features",
            datatype="GPFeatureLayer",
            parameterType="Optional",
            direction="Output")
        param4 = arcpy.Parameter(
            displayName="Output Generate by Actual Tool",
            name="in_ras_actual",
            datatype=["DERasterDataset", "GPRasterLayer"],
            parameterType="Optional",
            direction="Input")
        return [param0, param1, param2, param3, param4]

    def execute(self, parameters, messages):
        arcpy.AddMessage("Calculating")
        # get param cellsize
        if type(parameters[1].value) != float:
            if parameters[1].value is not None:
                param_cs = arcpy.sa.Raster(parameters[1].valueAsText)
            else:
                param_cs = None
        else:
            param_cs = parameters[1].value
        # get env cellsize
        if not parameters[2].valueAsText.replace('.', '', 1).isdigit() and parameters[2].valueAsText != "MINOF" and \
                parameters[2].valueAsText != "MAXOF":
            env_cs = arcpy.sa.Raster(parameters[2].valueAsText)
        else:
            if parameters[2].valueAsText == "MINOF" or parameters[2].valueAsText == "MAXOF":
                env_cs = None
            else:
                env_cs = parameters[2].value
        # get env snapraster
        if arcpy.env.snapRaster:
            env_snap = arcpy.sa.Raster(arcpy.env.snapRaster)
        else:
            env_snap = None
        # get env extent
        env_extent = arcpy.env.extent or "MINOF"
        try:
            arcpy.sa.Raster(parameters[0].valueAsText)
            isRas = True
        except:
            isRas = False
        if isRas:
            if param_cs is not None:
                cs_new, output_boundary = raster_check([arcpy.sa.Raster(parameters[0].valueAsText)],
                                                       env_ocs=arcpy.env.outputCoordinateSystem, env_cellsize=param_cs,
                                                       env_extent=env_extent, env_snapraster=env_snap)
            else:
                cs_new, output_boundary = raster_check([arcpy.sa.Raster(parameters[0].valueAsText)],
                                                       env_ocs=arcpy.env.outputCoordinateSystem, env_cellsize=env_cs,
                                                       env_extent=env_extent, env_snapraster=env_snap)
        else:
            cs_new, output_boundary = feature_check(parameters[0].valueAsText, param_cellsize=param_cs,
                                 env_ocs=arcpy.env.outputCoordinateSystem, env_cellsize=env_cs, env_extent=env_extent,
                                 env_snapraster=env_snap)

        arcpy.AddMessage("The expected raster cell size is {}".format(cs_new))
        if parameters[3].valueAsText is not None:
            arcpy.AddMessage("The extent of output raster (in polygon) has been added to the map.")
            arcpy.CopyFeatures_management(output_boundary, parameters[3].valueAsText)
        if parameters[4].valueAsText is not None:
            actual_ras = arcpy.sa.Raster(parameters[4].valueAsText)
            arcpy.AddMessage("The tool output raster cell size is {}".format(actual_ras.meanCellWidth))


class HillshadeVerify(object):
    def __init__(self):
        self.label = "Hillshade"
        self.description = "Verify cellsize and extent for Hillshade tool"
        self.canRunInBackground = True

    def getParameterInfo(self):
        param0 = arcpy.Parameter(
            displayName="Input raster",
            name="in_ras",
            datatype=["DERasterDataset", "GPRasterLayer"],
            parameterType="Required",
            direction="Input")
        param1 = arcpy.Parameter(
            displayName="Environment Cell Size",
            name="env_cs",
            datatype=["DERasterDataset", "GPRasterLayer", "GPDouble", "GPString"],
            parameterType="Required",
            direction="Input")
        param1.value = "MAXOF"
        param2 = arcpy.Parameter(
            displayName="Output Boundary",
            name="out_features",
            datatype="GPFeatureLayer",
            parameterType="Optional",
            direction="Output")
        param3 = arcpy.Parameter(
            displayName="Output Generate by Actual Tool",
            name="in_ras_actual",
            datatype=["DERasterDataset", "GPRasterLayer"],
            parameterType="Optional",
            direction="Input")
        return [param0, param1, param2, param3]

    def execute(self, parameters, messages):
        arcpy.env.overwriteOutput = True
        in_ras = arcpy.sa.Raster(parameters[0].valueAsText)
        arcpy.AddMessage("Calculating")
        # get env cellsize
        if not parameters[1].valueAsText.replace('.', '', 1).isdigit() and parameters[1].valueAsText != "MINOF" and \
                parameters[1].valueAsText != "MAXOF":
            env_cs = arcpy.sa.Raster(parameters[1].valueAsText)
        else:
            env_cs = parameters[1].value
        # get env snapraster
        if arcpy.env.snapRaster:
            env_snap = arcpy.sa.Raster(arcpy.env.snapRaster)
        else:
            env_snap = None
        # get env extent
        env_extent = arcpy.env.extent or "MINOF"
        cs_new, output_boundary = raster_check([in_ras], env_ocs=arcpy.env.outputCoordinateSystem,
                                               env_cellsize=env_cs, env_extent=env_extent,
                                               env_snapraster=env_snap)
        arcpy.AddMessage("The expected raster cell size is {}".format(cs_new))
        if parameters[2].valueAsText is not None:
            arcpy.AddMessage("The extent of output raster (in polygon) has been added to the map.")
            arcpy.CopyFeatures_management(output_boundary, parameters[2].valueAsText)
        if parameters[3].valueAsText is not None:
            actual_ras = arcpy.sa.Raster(parameters[3].valueAsText)
            arcpy.AddMessage("The tool output raster cell size is {}".format(actual_ras.meanCellWidth))


class FlowDirVerify(object):
    def __init__(self):
        self.label = "Flow Direction"
        self.description = "Verify cellsize and extent for Flow Direction tool"
        self.canRunInBackground = True

    def getParameterInfo(self):
        param0 = arcpy.Parameter(
            displayName="Input raster",
            name="in_ras",
            datatype=["DERasterDataset", "GPRasterLayer"],
            parameterType="Required",
            direction="Input")
        param1 = arcpy.Parameter(
            displayName="Environment Cell Size",
            name="env_cs",
            datatype=["DERasterDataset", "GPRasterLayer","GPString", "GPDouble"],
            parameterType="Required",
            direction="Input")
        param1.value = "MAXOF"
        param2 = arcpy.Parameter(
            displayName="Output Boundary",
            name="out_features",
            datatype="GPFeatureLayer",
            parameterType="Optional",
            direction="Output")
        param3 = arcpy.Parameter(
            displayName="Output Generate by Actual Tool",
            name="in_ras_actual",
            datatype=["DERasterDataset", "GPRasterLayer"],
            parameterType="Optional",
            direction="Input")
        return [param0, param1, param2, param3]

    def execute(self, parameters, messages):
        arcpy.env.overwriteOutput = True
        in_ras = arcpy.sa.Raster(parameters[0].valueAsText)
        arcpy.AddMessage("Calculating")
        # get env cellsize
        if not parameters[1].valueAsText.replace('.', '', 1).isdigit() and parameters[1].valueAsText != "MINOF" and \
                parameters[1].valueAsText != "MAXOF":
            env_cs = arcpy.sa.Raster(parameters[1].valueAsText)
        else:
            env_cs = parameters[1].value
        # get env snapraster
        if arcpy.env.snapRaster:
            env_snap = arcpy.sa.Raster(arcpy.env.snapRaster)
        else:
            env_snap = None
        # get env extent
        env_extent = arcpy.env.extent or "MINOF"
        cs_new, output_boundary = raster_check([in_ras], env_ocs=arcpy.env.outputCoordinateSystem,
                                               env_cellsize=env_cs, env_extent=env_extent,
                                               env_snapraster=env_snap)
        arcpy.AddMessage("The expected raster cell size is {}".format(cs_new))
        if parameters[2].valueAsText is not None:
            arcpy.AddMessage("The extent of output raster (in polygon) has been added to the map.")
            arcpy.CopyFeatures_management(output_boundary, parameters[2].valueAsText)
        if parameters[3].valueAsText is not None:
            actual_ras = arcpy.sa.Raster(parameters[3].valueAsText)
            arcpy.AddMessage("The tool output raster cell size is {}".format(actual_ras.meanCellWidth))


class FocalStatVerify(object):
    def __init__(self):
        self.label = "Focal Statistics"
        self.description = "Verify cellsize and extent for Focal Statistics tool"
        self.canRunInBackground = True

    def getParameterInfo(self):
        param0 = arcpy.Parameter(
            displayName="Input raster",
            name="in_ras",
            datatype=["DERasterDataset", "GPRasterLayer"],
            parameterType="Required",
            direction="Input")
        param1 = arcpy.Parameter(
            displayName="Environment Cell Size",
            name="env_cs",
            datatype=["DERasterDataset", "GPRasterLayer","GPString", "GPDouble"],
            parameterType="Required",
            direction="Input")
        param1.value = "MAXOF"
        param2 = arcpy.Parameter(
            displayName="Output Boundary",
            name="out_features",
            datatype="GPFeatureLayer",
            parameterType="Optional",
            direction="Output")
        param3 = arcpy.Parameter(
            displayName="Output Generate by Actual Tool",
            name="in_ras_actual",
            datatype=["DERasterDataset", "GPRasterLayer"],
            parameterType="Optional",
            direction="Input")
        return [param0, param1, param2, param3]

    def execute(self, parameters, messages):
        arcpy.env.overwriteOutput = True
        in_ras = arcpy.sa.Raster(parameters[0].valueAsText)
        arcpy.AddMessage("Calculating")
        # get env cellsize
        if not parameters[1].valueAsText.replace('.', '', 1).isdigit() and parameters[1].valueAsText != "MINOF" and \
                parameters[1].valueAsText != "MAXOF":
            env_cs = arcpy.sa.Raster(parameters[1].valueAsText)
        else:
            env_cs = parameters[1].value
        # get env snapraster
        if arcpy.env.snapRaster:
            env_snap = arcpy.sa.Raster(arcpy.env.snapRaster)
        else:
            env_snap = None
        # get env extent
        env_extent = arcpy.env.extent or "MINOF"
        cs_new, output_boundary = raster_check([in_ras], env_ocs=arcpy.env.outputCoordinateSystem,
                                               env_cellsize=env_cs, env_extent=env_extent,
                                               env_snapraster=env_snap)
        arcpy.AddMessage("The expected raster cell size is {}".format(cs_new))
        if parameters[2].valueAsText is not None:
            arcpy.AddMessage("The extent of output raster (in polygon) has been added to the map.")
            arcpy.CopyFeatures_management(output_boundary, parameters[2].valueAsText)
        if parameters[3].valueAsText is not None:
            actual_ras = arcpy.sa.Raster(parameters[3].valueAsText)
            arcpy.AddMessage("The tool output raster cell size is {}".format(actual_ras.meanCellWidth))


class ExtractByRectVerify(object):
    def __init__(self):
        self.label = "Extract By Rectangle"
        self.description = "Verify cellsize and extent for Extract By Rectangle tool"
        self.canRunInBackground = True

    def getParameterInfo(self):
        param0 = arcpy.Parameter(
            displayName="Input raster",
            name="in_ras",
            datatype=["DERasterDataset", "GPRasterLayer"],
            parameterType="Required",
            direction="Input")
        param1 = arcpy.Parameter(
            displayName="Environment Cell Size",
            name="env_cs",
            datatype=["DERasterDataset", "GPRasterLayer","GPString", "GPDouble"],
            parameterType="Required",
            direction="Input")
        param1.value = "MAXOF"
        param2 = arcpy.Parameter(
            displayName="Output Boundary",
            name="out_features",
            datatype="GPFeatureLayer",
            parameterType="Optional",
            direction="Output")
        param3 = arcpy.Parameter(
            displayName="Output Generate by Actual Tool",
            name="in_ras_actual",
            datatype=["DERasterDataset", "GPRasterLayer"],
            parameterType="Optional",
            direction="Input")
        return [param0, param1, param2, param3]

    def execute(self, parameters, messages):
        arcpy.env.overwriteOutput = True
        in_ras = arcpy.sa.Raster(parameters[0].valueAsText)
        arcpy.AddMessage("Calculating")
        # get env cellsize
        if not parameters[1].valueAsText.replace('.', '', 1).isdigit() and parameters[1].valueAsText != "MINOF" and \
                parameters[1].valueAsText != "MAXOF":
            env_cs = arcpy.sa.Raster(parameters[1].valueAsText)
        else:
            env_cs = parameters[1].value
        # get env snapraster
        if arcpy.env.snapRaster:
            env_snap = arcpy.sa.Raster(arcpy.env.snapRaster)
        else:
            env_snap = None
        # get env extent
        env_extent = arcpy.env.extent or "MINOF"
        cs_new, output_boundary = raster_check([in_ras], env_ocs=arcpy.env.outputCoordinateSystem,
                                               env_cellsize=env_cs, env_extent=env_extent,
                                               env_snapraster=env_snap)
        arcpy.AddMessage("The expected raster cell size is {}".format(cs_new))
        if parameters[2].valueAsText is not None:
            arcpy.AddMessage("The extent of output raster (in polygon) has been added to the map.")
            arcpy.CopyFeatures_management(output_boundary, parameters[2].valueAsText)
        if parameters[3].valueAsText is not None:
            actual_ras = arcpy.sa.Raster(parameters[3].valueAsText)
            arcpy.AddMessage("The tool output raster cell size is {}".format(actual_ras.meanCellWidth))


class IDWVerify(object):
    def __init__(self):
        self.label = "IDW"
        self.description = "Verify cellsize and extent for IDW tool"
        self.canRunInBackground = True

    def getParameterInfo(self):
        param0 = arcpy.Parameter(
            displayName="Input Source",
            name="in_data",
            datatype=["DEFeatureClass", "GPFeatureLayer"],
            parameterType="Required",
            direction="Input")
        param1 = arcpy.Parameter(
            displayName="Output cell size",
            name="param_cs",
            datatype=["DERasterDataset", "GPRasterLayer", "GPDouble"],
            parameterType="Optional",
            direction="Input")
        param2 = arcpy.Parameter(
            displayName="Environment Cell Size",
            name="env_cs",
            datatype=["DERasterDataset", "GPRasterLayer","GPString", "GPDouble"],
            parameterType="Required",
            direction="Input")
        param2.value = "MAXOF"
        param3 = arcpy.Parameter(
            displayName="Output Boundary",
            name="out_features",
            datatype="GPFeatureLayer",
            parameterType="Optional",
            direction="Output")
        param4 = arcpy.Parameter(
            displayName="Output Generate by Actual Tool",
            name="in_ras_actual",
            datatype=["DERasterDataset", "GPRasterLayer"],
            parameterType="Optional",
            direction="Input")
        return [param0, param1, param2, param3, param4]

    def execute(self, parameters, messages):
        arcpy.AddMessage("Calculating")
        # get param cellsize
        if type(parameters[1].value) != float:
            if parameters[1].value is not None:
                param_cs = arcpy.sa.Raster(parameters[1].valueAsText)
            else:
                param_cs = None
        else:
            param_cs = parameters[1].value
        # get env cellsize
        if not parameters[2].valueAsText.replace('.', '', 1).isdigit() and parameters[2].valueAsText != "MINOF" and \
                parameters[2].valueAsText != "MAXOF":
            env_cs = arcpy.sa.Raster(parameters[2].valueAsText)
        else:
            if parameters[2].valueAsText == "MINOF" or parameters[2].valueAsText == "MAXOF":
                env_cs = None
            else:
                env_cs = parameters[2].value
        # get env snapraster
        if arcpy.env.snapRaster:
            env_snap = arcpy.sa.Raster(arcpy.env.snapRaster)
        else:
            env_snap = None
        # get env extent
        env_extent = arcpy.env.extent

        cs_new, output_boundary = feature_check(parameters[0].valueAsText, param_cellsize=param_cs,
                                 env_ocs=arcpy.env.outputCoordinateSystem, env_cellsize=env_cs, env_extent=env_extent,
                                 env_snapraster=env_snap)

        arcpy.AddMessage("The expected raster cell size is {}".format(cs_new))
        if parameters[3].valueAsText is not None:
            arcpy.AddMessage("The extent of output raster (in polygon) has been added to the map.")
            arcpy.CopyFeatures_management(output_boundary, parameters[3].valueAsText)
        if parameters[4].valueAsText is not None:
            actual_ras = arcpy.sa.Raster(parameters[4].valueAsText)
            arcpy.AddMessage("The tool output raster cell size is {}".format(actual_ras.meanCellWidth))


class Point2RasterVerify(object):
    def __init__(self):
        self.label = "Point to Raster"
        self.description = "Verify cellsize and extent for Point to Raster tool"
        self.canRunInBackground = True

    def getParameterInfo(self):
        param0 = arcpy.Parameter(
            displayName="Input Source",
            name="in_data",
            datatype=["DEFeatureClass", "GPFeatureLayer"],
            parameterType="Required",
            direction="Input")
        param1 = arcpy.Parameter(
            displayName="Output cell size",
            name="param_cs",
            datatype=["DERasterDataset", "GPRasterLayer", "GPDouble"],
            parameterType="Optional",
            direction="Input")
        param2 = arcpy.Parameter(
            displayName="Environment Cell Size",
            name="env_cs",
            datatype=["DERasterDataset", "GPRasterLayer","GPString", "GPDouble"],
            parameterType="Required",
            direction="Input")
        param2.value = "MAXOF"
        param3 = arcpy.Parameter(
            displayName="Output Boundary",
            name="out_features",
            datatype="GPFeatureLayer",
            parameterType="Optional",
            direction="Output")
        param4 = arcpy.Parameter(
            displayName="Output Generate by Actual Tool",
            name="in_ras_actual",
            datatype=["DERasterDataset", "GPRasterLayer"],
            parameterType="Optional",
            direction="Input")
        return [param0, param1, param2, param3, param4]

    def execute(self, parameters, messages):
        arcpy.AddMessage("Calculating")
        # get param cellsize
        if type(parameters[1].value) != float:
            if parameters[1].value is not None:
                param_cs = arcpy.sa.Raster(parameters[1].valueAsText)
            else:
                param_cs = None
        else:
            param_cs = parameters[1].value
        # get env cellsize
        if not parameters[2].valueAsText.replace('.', '', 1).isdigit() and parameters[2].valueAsText != "MINOF" and \
                parameters[2].valueAsText != "MAXOF":
            env_cs = arcpy.sa.Raster(parameters[2].valueAsText)
        else:
            if parameters[2].valueAsText == "MINOF" or parameters[2].valueAsText == "MAXOF":
                env_cs = None
            else:
                env_cs = parameters[2].value
        # get env snapraster
        if arcpy.env.snapRaster:
            env_snap = arcpy.sa.Raster(arcpy.env.snapRaster)
        else:
            env_snap = None
        # get env extent
        env_extent = arcpy.env.extent

        cs_new, output_boundary = feature_check(parameters[0].valueAsText, param_cellsize=param_cs,
                                 env_ocs=arcpy.env.outputCoordinateSystem, env_cellsize=env_cs, env_extent=env_extent,
                                 env_snapraster=env_snap)

        arcpy.AddMessage("The expected raster cell size is {}".format(cs_new))
        if parameters[3].valueAsText is not None:
            arcpy.AddMessage("The extent of output raster (in polygon) has been added to the map.")
            arcpy.CopyFeatures_management(output_boundary, parameters[3].valueAsText)
        if parameters[4].valueAsText is not None:
            actual_ras = arcpy.sa.Raster(parameters[4].valueAsText)
            arcpy.AddMessage("The tool output raster cell size is {}".format(actual_ras.meanCellWidth))


class PointStatVerify(object):
    def __init__(self):
        self.label = "Point Statistics"
        self.description = "Verify cellsize and extent for Point Statistics tool"
        self.canRunInBackground = True

    def getParameterInfo(self):
        param0 = arcpy.Parameter(
            displayName="Input Source",
            name="in_data",
            datatype=["DEFeatureClass", "GPFeatureLayer"],
            parameterType="Required",
            direction="Input")
        param1 = arcpy.Parameter(
            displayName="Output cell size",
            name="param_cs",
            datatype=["DERasterDataset", "GPRasterLayer", "GPDouble"],
            parameterType="Optional",
            direction="Input")
        param2 = arcpy.Parameter(
            displayName="Environment Cell Size",
            name="env_cs",
            datatype=["DERasterDataset", "GPRasterLayer","GPString", "GPDouble"],
            parameterType="Required",
            direction="Input")
        param2.value = "MAXOF"
        param3 = arcpy.Parameter(
            displayName="Output Boundary",
            name="out_features",
            datatype="GPFeatureLayer",
            parameterType="Optional",
            direction="Output")
        param4 = arcpy.Parameter(
            displayName="Output Generate by Actual Tool",
            name="in_ras_actual",
            datatype=["DERasterDataset", "GPRasterLayer"],
            parameterType="Optional",
            direction="Input")
        return [param0, param1, param2, param3, param4]

    def execute(self, parameters, messages):
        arcpy.AddMessage("Calculating")
        # get param cellsize
        if type(parameters[1].value) != float:
            if parameters[1].value is not None:
                param_cs = arcpy.sa.Raster(parameters[1].valueAsText)
            else:
                param_cs = None
        else:
            param_cs = parameters[1].value
        # get env cellsize
        if not parameters[2].valueAsText.replace('.', '', 1).isdigit() and parameters[2].valueAsText != "MINOF" and \
                parameters[2].valueAsText != "MAXOF":
            env_cs = arcpy.sa.Raster(parameters[2].valueAsText)
        else:
            if parameters[2].valueAsText == "MINOF" or parameters[2].valueAsText == "MAXOF":
                env_cs = None
            else:
                env_cs = parameters[2].value
        # get env snapraster
        if arcpy.env.snapRaster:
            env_snap = arcpy.sa.Raster(arcpy.env.snapRaster)
        else:
            env_snap = None
        # get env extent
        env_extent = arcpy.env.extent

        cs_new, output_boundary = feature_check(parameters[0].valueAsText, param_cellsize=param_cs,
                                 env_ocs=arcpy.env.outputCoordinateSystem, env_cellsize=env_cs, env_extent=env_extent,
                                 env_snapraster=env_snap)

        arcpy.AddMessage("The expected raster cell size is {}".format(cs_new))
        if parameters[3].valueAsText is not None:
            arcpy.AddMessage("The extent of output raster (in polygon) has been added to the map.")
            arcpy.CopyFeatures_management(output_boundary, parameters[3].valueAsText)
        if parameters[4].valueAsText is not None:
            actual_ras = arcpy.sa.Raster(parameters[4].valueAsText)
            arcpy.AddMessage("The tool output raster cell size is {}".format(actual_ras.meanCellWidth))


class KernelDensityVerify(object):
    def __init__(self):
        self.label = "Kernel Density"
        self.description = "Verify cellsize and extent for Kernel Density tool"
        self.canRunInBackground = True

    def getParameterInfo(self):
        param0 = arcpy.Parameter(
            displayName="Input Source",
            name="in_data",
            datatype=["DEFeatureClass", "GPFeatureLayer"],
            parameterType="Required",
            direction="Input")
        param1 = arcpy.Parameter(
            displayName="Output cell size",
            name="param_cs",
            datatype=["DERasterDataset", "GPRasterLayer", "GPDouble"],
            parameterType="Optional",
            direction="Input")
        param2 = arcpy.Parameter(
            displayName="Environment Cell Size",
            name="env_cs",
            datatype=["DERasterDataset", "GPRasterLayer","GPString", "GPDouble"],
            parameterType="Required",
            direction="Input")
        param2.value = "MAXOF"
        param3 = arcpy.Parameter(
            displayName="Output Boundary",
            name="out_features",
            datatype="GPFeatureLayer",
            parameterType="Optional",
            direction="Output")
        param4 = arcpy.Parameter(
            displayName="Output Generate by Actual Tool",
            name="in_ras_actual",
            datatype=["DERasterDataset", "GPRasterLayer"],
            parameterType="Optional",
            direction="Input")
        return [param0, param1, param2, param3, param4]

    def execute(self, parameters, messages):
        arcpy.AddMessage("Calculating")
        # get param cellsize
        if type(parameters[1].value) != float:
            if parameters[1].value is not None:
                param_cs = arcpy.sa.Raster(parameters[1].valueAsText)
            else:
                param_cs = None
        else:
            param_cs = parameters[1].value
        # get env cellsize
        if not parameters[2].valueAsText.replace('.', '', 1).isdigit() and parameters[2].valueAsText != "MINOF" and \
                parameters[2].valueAsText != "MAXOF":
            env_cs = arcpy.sa.Raster(parameters[2].valueAsText)
        else:
            if parameters[2].valueAsText == "MINOF" or parameters[2].valueAsText == "MAXOF":
                env_cs = None
            else:
                env_cs = parameters[2].value
        # get env snapraster
        if arcpy.env.snapRaster:
            env_snap = arcpy.sa.Raster(arcpy.env.snapRaster)
        else:
            env_snap = None
        # get env extent
        env_extent = arcpy.env.extent

        cs_new, output_boundary = feature_check(parameters[0].valueAsText, param_cellsize=param_cs,
                                 env_ocs=arcpy.env.outputCoordinateSystem, env_cellsize=env_cs, env_extent=env_extent,
                                 env_snapraster=env_snap)

        arcpy.AddMessage("The expected raster cell size is {}".format(cs_new))
        if parameters[3].valueAsText is not None:
            arcpy.AddMessage("The extent of output raster (in polygon) has been added to the map.")
            arcpy.CopyFeatures_management(output_boundary, parameters[3].valueAsText)
        if parameters[4].valueAsText is not None:
            actual_ras = arcpy.sa.Raster(parameters[4].valueAsText)
            arcpy.AddMessage("The tool output raster cell size is {}".format(actual_ras.meanCellWidth))


class CellStatVerify(object):
    def __init__(self):
        self.label = "Cell Statistics"
        self.description = "Verify cellsize and extent for Cell Statistics tool"
        self.canRunInBackground = True

    def getParameterInfo(self):
        param0 = arcpy.Parameter(
            displayName="Input raster or constant value",
            name="in_ras_list",
            datatype=["DERasterDataset", "GPRasterLayer", "GPDouble"],
            parameterType="Required",
            direction="Input",
            multiValue=True)
        param1 = arcpy.Parameter(
            displayName="Environment Cell Size",
            name="env_cs",
            datatype=["DERasterDataset", "GPRasterLayer","GPString", "GPDouble"],
            parameterType="Required",
            direction="Input")
        param1.value = "MAXOF"
        param2 = arcpy.Parameter(
            displayName="Output Boundary",
            name="out_features",
            datatype="GPFeatureLayer",
            parameterType="Optional",
            direction="Output")
        param3 = arcpy.Parameter(
            displayName="Output Generate by Actual Tool",
            name="in_ras_actual",
            datatype=["DERasterDataset", "GPRasterLayer"],
            parameterType="Optional",
            direction="Input")
        return [param0, param1, param2, param3]

    def execute(self, parameters, messages):
        input_list = parameters[0].valueAsText.split(";")
        input_ras_list = list(map(lambda x: arcpy.sa.Raster(x), list(filter(lambda x: not x.isnumeric(), input_list))))
        if len(input_ras_list) == 0 and (parameters[1].value == "MAXOF" or parameters[1].value == "MINOF"
                                      or type(arcpy.env.extent) != arcpy.Extent):
            arcpy.AddError("Cell size and extent must be specified if all inputs are numeric values.")
        else:
            # get env cellsize
            if not parameters[1].valueAsText.replace('.', '', 1).isdigit() and parameters[1].valueAsText != "MINOF" and \
                    parameters[1].valueAsText != "MAXOF":
                env_cs = arcpy.sa.Raster(parameters[1].valueAsText)
            else:
                env_cs = parameters[1].value
            # get env snapraster
            if arcpy.env.snapRaster:
                env_snap = arcpy.sa.Raster(arcpy.env.snapRaster)
            else:
                env_snap = None
            # get env extent
            env_extent = arcpy.env.extent or "MINOF"
            cs_new, output_boundary = raster_check(input_ras_list, env_ocs=arcpy.env.outputCoordinateSystem,
                                               env_cellsize=env_cs, env_extent=env_extent, env_snapraster=env_snap)
            arcpy.AddMessage("The expected raster cell size is {}".format(cs_new))
            if parameters[2].valueAsText is not None:
                arcpy.AddMessage("The extent of output raster (in polygon) has been added to the map.")
                arcpy.CopyFeatures_management(output_boundary, parameters[2].valueAsText)
            if parameters[3].valueAsText is not None:
                actual_ras = arcpy.sa.Raster(parameters[3].valueAsText)
                arcpy.AddMessage("The tool output raster cell size is {}".format(actual_ras.meanCellWidth))


class CreateConstRasterVerify(object):
    def __init__(self):
        self.label = "Create Constant Raster"
        self.description = "Verify cellsize and extent for Create Constant Raster tool"
        self.canRunInBackground = True

    def getParameterInfo(self):
        param0 = arcpy.Parameter(
            displayName="Output Cell Size",
            name="param_cs",
            datatype=["DERasterDataset", "GPRasterLayer", "GPDouble"],
            parameterType="Required",
            direction="Input")
        param1 = arcpy.Parameter(
            displayName="Output Extent",
            name="param_extent",
            datatype=["GPExtent"],
            parameterType="Required",
            direction="Input")
        param2 = arcpy.Parameter(
            displayName="Output Boundary",
            name="out_features",
            datatype="GPFeatureLayer",
            parameterType="Optional",
            direction="Output")
        param3 = arcpy.Parameter(
            displayName="Output Generate by Actual Tool",
            name="in_ras_actual",
            datatype=["DERasterDataset", "GPRasterLayer"],
            parameterType="Optional",
            direction="Input")
        return [param0, param1, param2, param3]

    def execute(self, parameters, messages):
        if arcpy.env.snapRaster:
            env_snap = arcpy.sa.Raster(arcpy.env.snapRaster)
        else:
            env_snap = None
        cs_new, output_boundary = raster_check([], env_ocs=arcpy.env.outputCoordinateSystem,
                                               env_cellsize=parameters[0].value,
                                               env_extent=parameters[1].value, env_snapraster=env_snap)
        arcpy.AddMessage("The expected raster cell size is {}".format(cs_new))
        if parameters[2].valueAsText is not None:
            arcpy.AddMessage("The extent of output raster (in polygon) has been added to the map.")
            arcpy.CopyFeatures_management(output_boundary, parameters[2].valueAsText)
        if parameters[3].valueAsText is not None:
            actual_ras = arcpy.sa.Raster(parameters[3].valueAsText)
            arcpy.AddMessage("The tool output raster cell size is {}".format(actual_ras.meanCellWidth))


class ZonalStatVerify(object):
    def __init__(self):
        self.label = "Zonal Statistics"
        self.description = "Verify cellsize and extent for Zonal Statistics tool"
        self.canRunInBackground = True

    def getParameterInfo(self):
        param0 = arcpy.Parameter(
            displayName="Input raster or feature zone data",
            name="in_zone",
            datatype=["DERasterDataset", "DEFeatureClass", "GPFeatureLayer", "GPRasterLayer"],
            parameterType="Required",
            direction="Input")
        param1 = arcpy.Parameter(
            displayName="Input value raster",
            name="in_value",
            datatype=["DERasterDataset", "GPRasterLayer"],
            parameterType="Required",
            direction="Input")
        param2 = arcpy.Parameter(
            displayName="Environment Cell Size",
            name="env_cs",
            datatype=["DERasterDataset", "GPRasterLayer","GPString", "GPDouble"],
            parameterType="Required",
            direction="Input")
        param2.value = "MAXOF"
        param3 = arcpy.Parameter(
            displayName="Output Boundary",
            name="out_features",
            datatype="GPFeatureLayer",
            parameterType="Optional",
            direction="Output")
        param4 = arcpy.Parameter(
            displayName="Output Generate by Actual Tool",
            name="in_ras_actual",
            datatype=["DERasterDataset", "GPRasterLayer"],
            parameterType="Optional",
            direction="Input")
        return [param0, param1, param2, param3, param4]

    def execute(self, parameters, messages):

        arcpy.AddMessage("Calculating")

        # get env cellsize
        if not parameters[2].valueAsText.replace('.', '', 1).isdigit() and parameters[2].valueAsText != "MINOF" and \
                parameters[2].valueAsText != "MAXOF":
            env_cs = arcpy.sa.Raster(parameters[2].valueAsText)
        else:
            if parameters[2].valueAsText == "MINOF" or parameters[2].valueAsText == "MAXOF":
                env_cs = None
            else:
                env_cs = parameters[2].value
        # get env snapraster
        if arcpy.env.snapRaster:
            env_snap = arcpy.sa.Raster(arcpy.env.snapRaster)
        else:
            env_snap = arcpy.sa.Raster(parameters[1].valueAsText)
        # get env extent
        if arcpy.env.extent is None:
            env_extent = "MINOF"
        else:
            env_extent = arcpy.env.extent

        ras_value = arcpy.sa.Raster(parameters[1].valueAsText)
        try:
            arcpy.sa.Raster(parameters[0].valueAsText)
            isRas = True
        except:
            isRas = False
        if isRas:
            ras_zone = arcpy.sa.Raster(parameters[0].valueAsText)
            if arcpy.env.outputCoordinateSystem is None:
                env_ocs = ras_zone.spatialReference
            else:
                env_ocs = arcpy.env.outputCoordinateSystem
            cs_new, output_boundary = raster_check([ras_zone, ras_value],
                                                    env_ocs=env_ocs,
                                                    env_cellsize=env_cs,
                                                    env_extent=env_extent, env_snapraster=env_snap)
        else:
            if arcpy.env.outputCoordinateSystem is None:
                env_ocs = arcpy.Describe(parameters[0].valueAsText).spatialReference
            else:
                env_ocs = arcpy.env.outputCoordinateSystem
            # Get env_extent and calculate output_extent
            if env_extent == "MAXOF":
                output_boundary = calculate_output_extent_union([parameters[0].valueAsText,
                                                                 ras_value], env_ocs)
                cs_new, output_boundary = raster_check([ras_value],
                                                       env_ocs=env_ocs,
                                                       env_cellsize=env_cs,
                                                       env_extent=output_boundary.projectAs(ras_value.spatialReference)
                                                       .extent,
                                                       env_snapraster=env_snap)
            elif env_extent == "MINOF":
                output_boundary = calculate_output_extent_intersect([parameters[0].valueAsText,
                                                                     ras_value], env_ocs)
                cs_new, output_boundary = raster_check([ras_value],
                                                       env_ocs=env_ocs,
                                                       env_cellsize=env_cs,
                                                       env_extent=output_boundary.projectAs(ras_value.spatialReference)
                                                       .extent,
                                                       env_snapraster=env_snap)
            else:
                output_boundary = extent_to_polygon(env_extent.projectAs(env_ocs))
                cs_new, output_boundary = raster_check([ras_value],
                                                       env_ocs=env_ocs,
                                                       env_cellsize=env_cs,
                                                       env_extent=output_boundary.projectAs(ras_value.spatialReference)
                                                       .extent,
                                                       env_snapraster=env_snap)

        arcpy.AddMessage("The expected raster cell size is {}".format(cs_new))
        if parameters[3].valueAsText is not None:
            arcpy.AddMessage("The extent of output raster (in polygon) has been added to the map.")
            arcpy.CopyFeatures_management(output_boundary, parameters[3].valueAsText)
        if parameters[4].valueAsText is not None:
            actual_ras = arcpy.sa.Raster(parameters[4].valueAsText)
            arcpy.AddMessage("The tool output raster cell size is {}".format(actual_ras.meanCellWidth))
