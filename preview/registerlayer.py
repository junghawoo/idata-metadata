import os
import time
import pdb
import sys
import subprocess
from shutil import copyfile
import xml.etree.ElementTree as ET
from osgeo import gdal, gdal_array
import numpy as np
import numpy.ma as ma

from qgis.core import QgsApplication, QgsProject, QgsCoordinateReferenceSystem
from qgis.core import QgsRasterLayer, QgsVectorLayer,  QgsMapRendererSequentialJob, QgsMapSettings, QgsMapLayer,QgsLayerTreeGroup, QgsLayerTreeLayer, QgsGraduatedSymbolRenderer, QgsSingleBandGrayRenderer
from qgis.core import QgsMapLayerStyle, QgsContrastEnhancement, QgsRasterBandStats
from qgis.core import QgsRasterShader, QgsColorRampShader, QgsSingleBandPseudoColorRenderer

from qgis.PyQt.QtCore import pyqtRemoveInputHook
from qgis.PyQt.QtGui import QColor
from PyQt5 import QtCore
from PyQt5.QtXml import QDomDocument
from PyQt5.QtCore import Qt
import faulthandler

from oslo_concurrency import lockutils
from oslo_concurrency import processutils

# We limit maximum number of variables in netCDF to 10.
# Only first 10 variables are added to QGIS project file.
MAX_SUBDATASETS = 10
# data values smaller than LOWER_PERCENTILE will be colored same as LOWER_PERCENTILE
LOWER_PERCENTILE = 5
# data values greater than UPPER_PERCENTILE will be colored same as UPPER_PERCENTILE
UPPER_PERCENTILE = 95

RESULT_QGS_FILENAME = 'preview.qgs'
PATH = "/usr"

#on file creation
#create a preview.qgs project file and add a layer for the given filename
#if preview.qgs already exists in the directory, update a layer only.
#on file deletion
#remove layer from preview.qgs
#mode = 1 => create
#mode = -1 => delete
# THIS FUNCTION IS NOT THREAD SAFE SINCE IT READS/UPDATES THE QGS FILE
# the lockfile geoedf_preview is stored in a persistent directory /srv/idata/workerfiles/previewlocks
# persistent dir is needed since lock needs to be coordinated across worker containers
@lockutils.synchronized('geoedf_preview', fair=True, external=True)
def update_qgs(geospatial_filename,hub,mode=1):

    with open('/tmp/messages.txt','a+') as logfile:
        logfile.write('\n preview: %s' % geospatial_filename)

    # figure out the project directory
    project_dir = os.path.split(geospatial_filename)[0]

    try:

        # find the current QGS project file in the directory
        # rename it with the latest timestamp
        project_qgs_filename = None #default filename
        for file in os.listdir(project_dir):
            if file.endswith('.qgs'):
                project_qgs_filename = file
                break

        #construct new QGS project filename
        #we need to create a new file each time due to QGIS caching of GetProjectSettings
        new_project_qgs_filename = '%s_%s' % (str(int(time.time())),RESULT_QGS_FILENAME)
        new_projectfile_path = os.path.join(project_dir, new_project_qgs_filename)

        # need to delete the previous qgs file if exists
        delete_old_qgsfile = False

        # if a project file exists, use that
        if project_qgs_filename is not None:
            with open('/tmp/messages.txt','a+') as logfile:
                logfile.write('\n qgs file already exists here')
            projectfile_path = os.path.join(project_dir,project_qgs_filename)
            delete_old_qgsfile = True
        else:
            with open('/tmp/messages.txt','a+') as logfile:
                logfile.write('\n qgs file does not exist')
            projectfile_path = os.path.join(project_dir, new_project_qgs_filename)

        with open('/tmp/messages.txt','a+') as logfile:
            logfile.write('\n old preview: %s' % projectfile_path)
            logfile.write('\n new preview: %s' % new_projectfile_path)

        QgsApplication.setPrefixPath(PATH, True)
        # second argument to False disables the GUI
        app = QgsApplication([], False, None)
        app.initQgis()
        project = QgsProject.instance()
        project.clear()

        if mode == 1: #create
            # Load project information if RESULT_QGS_FILENAME exists

            if os.path.exists(projectfile_path):
                with open('/tmp/messages.txt','a+') as logfile:
                    logfile.write('\n loading existing project from %s' % projectfile_path)
                project.read(projectfile_path)
            else:
                with open('/tmp/messages.txt','a+') as logfile:
                    logfile.write('\n initializing project')
                #project = initialize_project()
                project.writeEntryBool("WMSServiceCapabilities","/", True)

                project.writeEntry("WMSContactMail","", "wooj@purdue.edu")

                manual_extent=[ "-180", "-90", "180", "90"]
                project.writeEntry("WMSExtent",'', manual_extent)
                project.writeEntry("WMSImageQuality", '', 90)
                # height, width are increased to handle 4K resolution
                project.writeEntry("WMSMaxHeight", '',2160)
                project.writeEntry("WMSMaxWidth",'',3840)
                project.writeEntry("WMSPrecision",'', "8")
                project.writeEntryBool("WMSAddWktGeometry","/", True)

                crsList = ["EPSG:4326", "EPSG:3857"]
                project.writeEntry("WMSCrsList","", crsList)
                project.writeEntryBool("WMSSegmentizeFeatureInfoGeometry",'', False)

                crs = QgsCoordinateReferenceSystem("EPSG:4326")

                project.setCrs( crs )
                project.writeEntry('WFSLayers', "/", [])

                project.writeEntry("WMSServiceTitle","", "Preview")

            filename_without_extension = os.path.splitext(os.path.split(geospatial_filename)[1])[0]
            len_to_match = len(filename_without_extension)

            for id, layer in project.mapLayers().items():
                with open('/tmp/messages.txt','a+') as logfile:
                    logfile.write('\n old layer :%s' % layer.name())
                # Check if this layer has the geospatial filename set aside file extension
                if layer.name()[0:len_to_match] == filename_without_extension :
                    # Match found
                    with open('/tmp/messages.txt','a+') as logfile:
                        logfile.write('\n layer already found in project: %s' % filename_without_extension)
                    app.exit()
                    return

            id = None
            layer = None

            if geospatial_filename.endswith(".tif"):

                layername_to_register ='{0}_TIF'.format(filename_without_extension)
                layer = QgsRasterLayer(geospatial_filename, layername_to_register)

                if not layer.isValid():
                    app.exit()
                    return

                if layer.crs() is None:
                    # set layer's Coordinate Reference system to epsg 4326
                    layer.setCrs(QgsCoordinateReferenceSystem.fromEpsgId(4326))

                # set color ramp for the layer
                set_color_ramp(layer, geospatial_filename)

                style_manager = layer.styleManager()
                style = QgsMapLayerStyle()
                style.readFromLayer(layer)
                style_manager.addStyle("mystyle", style)

                project.addMapLayer(layer)
                # set mapcanvas's crs to layer's crs
                set_map_canvas(layer)

            elif geospatial_filename.endswith(".shp"):

                layername_to_register ='{0}_SHP'.format(filename_without_extension)
                layer = QgsVectorLayer(geospatial_filename, layername_to_register, 'ogr')

                if layer.isValid():
                    if layer.crs() is None:
                        # set layer's Coordinate Reference system to epsg 4326
                        layer.setCrs(QgsCoordinateReferenceSystem.fromEpsgId(4326))
                    add_to_wfs_layers(layer)
                    project.addMapLayer(layer)
                    # set mapcanvas's crs to layer's crs
                    set_map_canvas(layer)

        else: #delete mode
            # Load project information if RESULT_QGS_FILENAME exists

            if os.path.exists(projectfile_path):
                project.read(projectfile_path)
            else:
                # if qgs file does not exist, no need to remove a layer
                # ignore request and just return
                app.exit()
                return

            # Find a matching layername from the tree and remove that layer if found
            # File extension was added uppercase so we prepare a layername ending with uppercase extension
            # XXX.tif -> XXX_TIF
            # YYY.shp -> YYY_SHP
            # ZZZ.nc  -> ZZZ_NC

            # os.path.split() splits a string into head and tail where the tail is the filename with extension
            filename_without_extension, ext = os.path.splitext(os.path.split(geospatial_filename)[1])
            layername_to_match ='{0}_{1}'.format(filename_without_extension, ext.replace('.', '').upper())
            len_to_match = len(layername_to_match)

            for id, layer in project.mapLayers().items():
                # Check if this layer has the geospatial filename set aside file extension
                if layer.name()[0:len_to_match] == layername_to_match :
                    # TIF or SHP has only one layer
                    remove_wfs_layers(layer)
                    project.removeMapLayer(id)

                    # update qgsproject crs
                    toplayer = get_top_layer()
                    if toplayer != None:
                        set_map_canvas(toplayer)
                    else:
                        #set default crs to 4326
                        QgsProject.instance().setCrs(QgsCoordinateReferenceSystem.fromEpsgId(4326))

        #update changes to QGS file and then get updated themes.json
        with open('/tmp/messages.txt','a+') as logfile:
            logfile.write('\n going to write project file')
        # always write to new QGS project filepath
        boolWrite = project.write(new_projectfile_path)
        # delete the old QGS file
        if delete_old_qgsfile:
            os.remove(projectfile_path)

        # also delete the themes.json so that we can check when themesConfig has succeeded
        if os.path.exists('/app/qwc2-demo-app/themes.json'):
            os.remove('/app/qwc2-demo-app/themes.json')

        if os.path.exists('/app/qwc2-demo-app/themesConfig.json'):
            os.remove('/app/qwc2-demo-app/themesConfig.json')

        with open('/tmp/messages.txt','a+') as logfile:
            logfile.write('\n removed themes file')

        # figure out QGIS server from env
        qgis_server = os.getenv('QGIS_SERVER','qgis-server')

        # copy themesConfig template to /tmp
        # search replace for URL and project folder
        # run themesconfig with appropriate path
        # copy resulting themes file to project folder
        # update .qgs file in project folder
        tmp_themes_config = '/app/qwc2-demo-app/themesConfig.json'
        with open(tmp_themes_config,'w') as tmp_themes_config_file:
            themes_config = '/app/themesConfig.json'
            with open(themes_config,'r') as themes_config_file:
                for line in themes_config_file:
                    # replace QGIS_SERVER and PROJ_QGS_FILE
                    if 'QGIS_SERVER' in line:
                        line = line.replace('QGIS_SERVER',qgis_server)
                    if 'PROJ_QGS_FILE' in line:
                        line = line.replace('PROJ_QGS_FILE',new_projectfile_path)
                    if 'HUB' in line:
                        line = line.replace('HUB',hub)
                    tmp_themes_config_file.write(line)

        with open('/tmp/messages.txt','a+') as logfile:
            logfile.write('\n going to try yarn run')

        # run themesconfig with cwd = /app/qwc2-demo-app
        # this is retried a couple of times until themes.json is created
        # temp fix for the intermittent host unreachable error when trying to GetProjectSettings
        for retry in range(10):
            with open('/tmp/messages.txt','a+') as logfile:
                logfile.write('\nretrying yarn run %d' % retry)
            subprocess.run(['yarn','run','themesconfig'],cwd='/app/qwc2-demo-app')
            # if success, break out
            if os.path.exists('/app/qwc2-demo-app/themes.json'):
                with open('/tmp/messages.txt','a+') as logfile:
                    logfile.write('yarn run succeeded, themes.json created')
                # copy the themes.json file from /tmp to the project directory
                copyfile('/app/qwc2-demo-app/themes.json','%s/themes.json' % project_dir)
                break

        layer = None

        # clean up layers
        for layer in project.mapLayers().values():
            del layer

        # 03/02/2021
        # if objects are not deleted, python tries to free objects after program ends
        # therefore either not calling exitQgis() or freeing objects explicitly can prevent segmentation faults.
        #app.exitQgis()
        app.exit()
        add_legends(new_projectfile_path)

    except Exception as exc:
        # delete the qgs and themes file since we cannot guarantee consistent preview
        for file in os.listdir(project_dir):
            if file.endswith('.qgs'):
                qgs_file = '%s/%s' % (project_dir,file)
                os.remove(qgs_file)
        if os.path.exists('%s/themes.json' % project_dir):
            os.remove('%s/themes.json' % project_dir)
        # create a preview error file and write out exception
        with open('%s/preview.err' % project_dir,'a+') as errfile:
            errfile.write('Exception when previewing %s: %s' % (geospatial_filename,exc))

#set default CRS to 4326
def set_project_crs():
    QgsProject.instance().setCrs(QgsCoordinateReferenceSystem('EPSG:4326'))

# add a vector layer to WFS list
# Must invoke this function when layer has not been deleted
def add_to_wfs_layers(layer):
    #print("Adding WFS capability for the layer layer id: %s" %(layer.id()))

    project = QgsProject.instance()


    wfs_layers, doesExist = project.readListEntry("WFSLayers",'')
    #print("existing_layers:", wfs_layers)

    if doesExist == False:
        #print("wfs_layers:", wfs_layers)
        wfs_layers =[]

    #print("wfs_layers:", wfs_layers)
    wfs_layers.append( layer.id())

    project.writeEntry("WFSLayers",'', wfs_layers)
    project.writeEntry("WFSLayersPrecision", layer.id(), 8 )

# remove a layer from WFS list
# Must invoke this function when layer has not been deleted
# when vector layer is inputed, it does not do anything
def remove_wfs_layers(layer):
    #print("Removing WFS capability for the layer id: %s" %(layer.id()))

    project = QgsProject.instance()

    wfs_layers, doesExist = project.instance().readListEntry("WFSLayers",'')
    #print("existing_layers:", wfs_layers)

    if doesExist == True:
        #print("wfs_layers before remove:", wfs_layers)

        try:
            wfs_layers.remove( layer.id())
            #print("wfs_layers after remove:", wfs_layers)
            # update wfslayers
            project.writeEntry("WFSLayers",'', wfs_layers)
            project.removeEntry("WFSLayersPrecision", layer.id() )
        # ignore when trying to remove WFS for TIF files
        except ValueError:
            pass  # do nothing!

def add_legends(projectfile_path):
    """ This function makes each layer's legend displayed in legend box
        It finds all layers inside given projectfile_path, and make every layer visible
    """
    #faulthandler.enable()

    with open( projectfile_path, 'rb') as xml_file:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        layers = root.findall('./layer-tree-group/layer-tree-layer')
        layers_dict={}

        for layer in layers:
            layers_dict.update({ layer.get('name'): layer.get('id')})

        layer = None
        layers = None

    for child in root:
        if child.tag == 'properties':
            legend = ET.SubElement(child, 'legend', {"updateDrawingOrder":"true"})
            #legend = ET.SubElement(child, 'legend')

            for key in layers_dict:
                legendlayer = ET.SubElement(legend, 'legendlayer', {"drawingOrder":"-1",  "showFeatureCount":"0", "checked":"Qt::Checked", "name": key, "open": "true"})

                if legendlayer is not None:
                    filegrouplayer = ET.SubElement(legendlayer, 'filegroup', {"hidden":"false",   "open": "true"})
                    if filegrouplayer is not None:
                        legendlayerfile =  ET.SubElement(filegrouplayer, 'legendlayerfile', {"layerid": layers_dict[key], "isInOverview":"1",  "visible": "1"})

    with open( projectfile_path, 'w') as f:
        tree.write(f, encoding='unicode')

def initialize_project():
    project = QgsProject.instance()
    project.writeEntryBool("WMSServiceCapabilities","/", True)

    project.writeEntry("WMSContactMail","", "wooj@purdue.edu")

    manual_extent=[ "-180", "-90", "180", "90"]
    project.writeEntry("WMSExtent",'', manual_extent)
    project.writeEntry("WMSImageQuality", '', 90)
    # height, width are increased to handle 4K resolution
    project.writeEntry("WMSMaxHeight", '',2160)
    project.writeEntry("WMSMaxWidth",'',3840)
    project.writeEntry("WMSPrecision",'', "8")
    project.writeEntryBool("WMSAddWktGeometry","/", True)

    crsList = ["EPSG:4326", "EPSG:3857"]
    project.writeEntry("WMSCrsList","", crsList)
    project.writeEntryBool("WMSSegmentizeFeatureInfoGeometry",'', False)


    crs = QgsCoordinateReferenceSystem("EPSG:4326")

    project.setCrs( crs )


#https://gis.stackexchange.com/questions/130632/using-qgis-legendinterface-from-standalone
    #render = QgsMapRendererSequentialJob(settings)
    project.writeEntry('WFSLayers', "/", [])
    pWfsLayer =[]
    layers =[]

    return project

def set_map_canvas(layer):

    if layer is None:
        return

    crs = layer.crs()
    if crs is None:
        # set layer's Coordinate Reference system to epsg 4326
        crs = QgsCoordinateReferenceSystem.fromEpsgId(4326)

    QgsProject.instance().setCrs( crs )

    # it does not seem to work.
    # In a standalone app, iface is not initialized and qgis app has no default canvas
    # https://gis.stackexchange.com/questions/363363/difference-between-iface-mapcanvas-and-qgsmapcanvas
    # canvas = QgsMapCanvas()
    # canvas.setCanvasColor(Qt.white)
    # canvas.setDestinationCrs(crs)
    #
    # # do we need to set these?
    # settings = canvas.mapSettings()
    # settings.setFlag(QgsMapSettings.DrawLabeling, False)
    # settings.setFlag(QgsMapSettings.Antialiasing, True)


def get_top_layer():

    project =  QgsProject.instance()
    layers = project.layerTreeRoot()

    if len(layers.children()) == 0 :
        return None
    else:
        return layers.children()[0].layer()

def set_color_ramp(layer, filepath):
    # create a pseudo color ramp and apply them to the layer.
    # filepath is used by numpy array functions to get percentile values
    # for the minimum and maximum thresholds

    if not layer.isValid():
        return

    provider = layer.dataProvider()
    extent = layer.extent()

    # 04/12/2021
    # Is it right to update extent if new layer is added ?
    #
    #canvas.setExtent(extent)

    ver = provider.hasStatistics(1, QgsRasterBandStats.All)

    stats = provider.bandStatistics(1, QgsRasterBandStats.All,extent, 0)

    if (stats.minimumValue < 0):
        min = 0

    else:
        min= stats.minimumValue

    max = stats.maximumValue
    value_range = max - min
    step = value_range/4.0
    interval = min + step

    percentiles = [ LOWER_PERCENTILE, UPPER_PERCENTILE]

    sds = gdal.Open(filepath, gdal.GA_ReadOnly)

    if sds is None:
        return

    rasterArray = sds.ReadAsArray(0,0, sds.RasterXSize, sds.RasterYSize )

    # Set NoData Value
    band = sds.GetRasterBand(1)
    nodata = band.GetNoDataValue()

    # replace nodatavalue with nan so that
    # outliers cannot affect the color ramp selection
    # https://currents.soest.hawaii.edu/ocn_data_analysis/_static/masked_arrays.html
    rasterArray = np.ma.masked_equal(rasterArray, nodata)
    nan_array = np.ma.filled( rasterArray.astype(float), np.nan)

    # after ignoring nan values, get corresponding percentiles
    adjusted_min = np.nanpercentile(nan_array, LOWER_PERCENTILE)
    adjusted_max = np.nanpercentile(nan_array, UPPER_PERCENTILE)
    adjusted_range = np.nanpercentile(nan_array, UPPER_PERCENTILE) - np.nanpercentile(nan_array, LOWER_PERCENTILE)
    adjusted_step = adjusted_range/4.0

    #close subdataset
    sds = None
    rasterArray = None
    nan_array = None

    colDic = {'Fire engine red':'#d7191c',
              'Fire engine red':'#d7191c',
              'Rajah':'#fdae61',
              'Cumulus': '#ffffbf',
              'Moss green': '#abdda4',
              'Curious blue':'#2b83ba',
              'Curious blue':'#2b83ba',}

    valueList =[min, adjusted_min, adjusted_min+adjusted_step, adjusted_min+2*adjusted_step, adjusted_min+3*adjusted_step, adjusted_max,  max]
    print (valueList)

    lst = [ QgsColorRampShader.ColorRampItem(valueList[0], QColor(colDic['Fire engine red'])),
            QgsColorRampShader.ColorRampItem(valueList[1], QColor(colDic['Fire engine red'])),
            QgsColorRampShader.ColorRampItem(valueList[2], QColor(colDic['Rajah'])),
            QgsColorRampShader.ColorRampItem(valueList[3], QColor(colDic['Cumulus'])),
            QgsColorRampShader.ColorRampItem(valueList[4], QColor(colDic['Moss green'])),
            QgsColorRampShader.ColorRampItem(valueList[5], QColor(colDic['Curious blue'])),
            QgsColorRampShader.ColorRampItem(valueList[6], QColor(colDic['Curious blue']))
            ]

    myRasterShader = QgsRasterShader()
    myColorRamp = QgsColorRampShader()

    myColorRamp.setColorRampItemList(lst)
    myColorRamp.setClassificationMode(QgsColorRampShader.EqualInterval)
    myColorRamp.setColorRampType(QgsColorRampShader.Interpolated)
    myRasterShader.setRasterShaderFunction(myColorRamp)

    myPseudoRenderer = QgsSingleBandPseudoColorRenderer(layer.dataProvider(),
                                                        1,
                                                        myRasterShader)

    layer.setRenderer(myPseudoRenderer)
