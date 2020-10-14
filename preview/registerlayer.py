import os
import subprocess
from shutil import copyfile
import pdb
# MUST be executed with python3
#home = os.path.expanduser('~')
#PATH = os.path.join(home, 'miniconda2', 'envs', 'qgis', 'share', 'qgis', 'python')
#PATH = "/usr/share/qgis/python"
PATH="/usr"
import sys
import xml.etree.ElementTree as ET
#sys.path.append(PATH)

from qgis.core import QgsApplication, QgsProject, QgsCoordinateReferenceSystem
from qgis.core import QgsRasterLayer, QgsVectorLayer,  QgsMapRendererSequentialJob, QgsMapSettings, QgsMapLayer,QgsLayerTreeGroup, QgsLayerTreeLayer, QgsGraduatedSymbolRenderer, QgsSingleBandGrayRenderer
from qgis.core import QgsMapLayerStyle, QgsContrastEnhancement, QgsRasterBandStats

from qgis.utils import iface
from qgis.gui import QgsMapCanvas
from qgis.PyQt.QtCore import pyqtRemoveInputHook, Qt
#from PyQt5 import QtCore
#from PyQt5.QtXml import QDomDocument
#from PyQt5.QtCore import QTimer, QSize


""" This python code adds a new raster or shape file as a layer to the existing
    preview.qgs.
    If preview.qgs does not exist in the directory of the given geospatial file,
    it creates new RESULT_QGS_FILENAME.

    It assumes that host directory for a geospatial file is mapped to
    /idata_project_dir.

    Argument 'geospatial_filename' is the os.path.basename(geospatial_file_path).
    If geospatial_file_path is the host file's path /foo/bar/item.tiff,
    /idata_project_dir is os.path.dirname(geospatial_file_path) or /foo/bar,
    and geospatial_filename is item.tiff
"""


os.environ['QT_QPA_PLATFORM'] = 'offscreen'
RESULT_QGS_FILENAME = 'preview.qgs'

def update_qgs(geospatial_filename):

    # figure out the project directory
    project_dir = os.path.split(geospatial_filename)[0]
    projectfile_path = os.path.join(project_dir, RESULT_QGS_FILENAME)

    # enable these for debugging
    #pyqtRemoveInputHook()
    #pdb.set_trace()
    #QgsApplication.setPrefixPath(PATH, True)
    # second argument to False disables the GUI
    qgs = QgsApplication([], False)
    #qgs = QgsApplication([], True)

    qgs.initQgis()

    project = QgsProject.instance()

    project.writeEntryBool("WMSServiceCapabilities","/", True)
    # full path contains delimiters which is not good for title.
    # I am replacing slashes with dashes, and use the replaced string as unique title for the QGS filename
    project.writeEntry("WMSServiceTitle","", project_dir.replace('/','-'))
    project.writeEntry("WMSContactMail","", "wooj@purdue.edu")
    project.writeEntry("WMSOnlineResource","","")

    manual_extent=[ "-180", "-90", "180", "90"]
    project.writeEntry("WMSExtent",'', manual_extent)
    project.writeEntry("WMSImageQuality", '', 90)
    project.writeEntry("WMSMaxHeight", '',960)
    project.writeEntry("WMSMaxWidth",'',1280)
    project.writeEntry("WMSPrecision",'', "8")
    project.writeEntryBool("WMSAddWktGeometry","/", True)

    crsList = ["EPSG:4326"]
    project.writeEntry("WMSCrsList","", crsList)
    project.writeEntryBool("WMSSegmentizeFeatureInfoGeometry",'', False)

    crs = QgsCoordinateReferenceSystem("EPSG:4326")

    QgsProject.instance().setCrs( crs )
    canvas = QgsMapCanvas()
    canvas.setCanvasColor(Qt.white)
    canvas.setDestinationCrs(crs)

    settings = canvas.mapSettings()
    #settings.setOutputSize( QSize(1000,1000))
    settings.setFlag(QgsMapSettings.DrawLabeling, False)
    settings.setFlag(QgsMapSettings.Antialiasing, True)

#https://gis.stackexchange.com/questions/130632/using-qgis-legendinterface-from-standalone
    #render = QgsMapRendererSequentialJob(settings)
    QgsProject.instance().writeEntry('WFSLayers', "/", [])
    pWfsLayer =[]
    layers =[]

    # QgsGraduatedSymbolRenderer seems to be only for SHP file
    renderer = QgsGraduatedSymbolRenderer()
    renderer.setMode(QgsGraduatedSymbolRenderer.EqualInterval)

    # filename is unique in a directory so it can be used as unique layername
    # splitext() returns filename without extension and this will be used as layername
    filename_without_extension = os.path.splitext(os.path.split(geospatial_filename)[1])[0]

    if geospatial_filename.endswith(".tif"):

        layer = QgsRasterLayer(geospatial_filename, filename_without_extension)

        # set layer's Coordinate Reference system to epsg 4326
        layer.setCrs(QgsCoordinateReferenceSystem.fromEpsgId(4326))


        provider = layer.dataProvider()
        extent = layer.extent()
        canvas.setExtent(extent)

        ver = provider.hasStatistics(1, QgsRasterBandStats.All)

        stats = provider.bandStatistics(1, QgsRasterBandStats.All,extent, 0)

        if (stats.minimumValue < 0):
            min = 0

        else:
            min= stats.minimumValue

        max = stats.maximumValue
        range = max - min
        add = range//2
        interval = min + add



        raster_renderer = QgsSingleBandGrayRenderer( layer.dataProvider(), 1)
        # contrast enhancement
        ce = QgsContrastEnhancement(layer.dataProvider().dataType(0))
        ce.setContrastEnhancementAlgorithm(QgsContrastEnhancement.StretchToMinimumMaximum)
        ce.setMinimumValue(min)
        ce.setMaximumValue(max)
        raster_renderer.setContrastEnhancement(ce)

        #raster_renderer.setMode(QgsGraduatedSymbolRenderer.EqualInterval)
        #renderer.updateClasses(layer, QgsGraduatedSymbolRenderer.EqualInterval, 10)
        layer.setRenderer(raster_renderer)

        style_manager = layer.styleManager()
        style = QgsMapLayerStyle()
        style.readFromLayer(layer)
        style_manager.addStyle("mystyle", style)

        if layer.isValid():
            project.addMapLayer(layer)

    elif geospatial_filename.endswith(".shp"):

        layer = QgsVectorLayer(geospatial_filename, filename_without_extension, 'ogr')
        # set layer's Coordinate Reference system to epsg 4326
        layer.setCrs(QgsCoordinateReferenceSystem.fromEpsgId(4326))

        if layer.isValid():
            QgsProject.instance().addMapLayer(layer)

    layers = project.mapLayers()
    map_canvas_layer_list = [ l for l in layers.values() ]
    canvas.setLayers(map_canvas_layer_list)

    #for layer, name in zip(QgsProject.instance().mapLayers().values(), keys):
    #    layer.loadNamedStyle(os.path.join(qml, '{}{}'.format(qml, '.qml')))
    #QgsApplication.instance().processEvents()

    #QTimer.singleShot(10, set_project_crs)
    #set project's Coordinate Reference system to epsg 4326
    #QgsProject.instance().setCrs( crs)

    QgsApplication.instance().processEvents()
    boolWrite = project.write(projectfile_path)
    
    #qgs.exitQgis()

    qgs.exit()

    tree = ET.parse(projectfile_path)
    root = tree.getroot()

    layers = root.findall('./layer-tree-group/layer-tree-layer')
    layers_dict={}

    for layer in layers:
        layers_dict.update({ layer.get('name'): layer.get('id')})

    for child in root:
        if child.tag == 'properties':
            legend = ET.SubElement(child, 'legend', {"updateDrawingOrder":"true"})

            for key in layers_dict:
                legendlayer = ET.SubElement(legend, 'legendlayer', {"drawingOrder":"-1",  "showFeatureCount":"0", "checked":"Qt::Checked", "name": key, "open": "true"})
                filegrouplayer = ET.SubElement(legendlayer, 'filegroup', {"hidden":"false",   "open": "true"})
                legendlayerfile =  ET.SubElement(filegrouplayer, 'legendlayerfile', {"layerid": layers_dict[key], "isInOverview":"1",  "visible": "1"})

    tree.write(projectfile_path)

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
                    line = line.replace('PROJ_QGS_FILE',projectfile_path)
                tmp_themes_config_file.write(line)

    # run themesconfig with cwd = /tmp
    subprocess.run(['yarn','run','themesconfig'],cwd='/app/qwc2-demo-app')

    # copy the themes.json file from /tmp to the project directory
    copyfile('/app/qwc2-demo-app/themes.json','%s/themes.json' % project_dir)

def set_project_crs():
    QgsProject.instance().setCrs(QgsCoordinateReferenceSystem('EPSG:4326'))
