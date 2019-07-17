# -*- coding: utf-8 -*-
"""
/***************************************************************************
 AnimalMovementAnalysis
                                 A QGIS plugin
 This plugin finds correlation between air temperature and activity patterns
 of animals chosen by the user in the area of North Rhine-Westphalia
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2019-06-23
        git sha              : $Format:%H$
        copyright            : (C) 2019 by Aditya Rajendra Kudekar,
        Violeta Ana Luz Sosa León, Tina Baidar, Muhammad Saad Saif,
        Anna Formaniuk
        email                : a_form03@uni-muenster.de
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import sys
import processing
from PyQt5.QtCore import (QSettings, QTranslator, qVersion, QCoreApplication,
                          QVariant)
from PyQt5.QtGui import QIcon, QImage, QPixmap
from PyQt5.QtWidgets import QAction

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialogs
from .movement_analysis_dialog import (AnimalMovementAnalysisDialog,
                                       AnimalMovementAnalysisDialogFilter,
                                       AnimalMovementAnalysisDialogResults)

from qgis.core import (QgsProject, QgsColorRampShader,
                       Qgis, QgsVectorLayer, QgsRasterLayer,
                       QgsSingleBandPseudoColorRenderer,
                       QgsVectorDataProvider, QgsField)

from datetime import datetime as dt

import qgis.utils
import os

import matplotlib.pyplot as plt
plt.clf()
# from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
# from matplotlib.figure import Figure

# import local processing files
sys.path.insert(0, './preprocessing')
sys.path.insert(0, './processing')
sys.path.insert(0, '.postprocessing')

try:
    from .preprocessing import preprocessing_new as preproces
    from .processing import processing_analysis as proces
    from .postprocessing import avgDistancePerMonthPlot as month_plot
    from .postprocessing import avgDistancePerTempPlot as temp_plot
    from .postprocessing import scatterPlotWithFitting as scatter_plot
except:
    raise


class AnimalMovementAnalysis:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'AnimalMovementAnalysis_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Animal Movement Analysis')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('AnimalMovementAnalysis', message)

    def add_action(self,
                   icon_path,
                   text,
                   callback,
                   enabled_flag=True,
                   add_to_menu=True,
                   add_to_toolbar=True,
                   status_tip=None,
                   whats_this=None,
                   parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/movement_analysis/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Analyse Animal Movement'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Animal Movement Analysis'),
                action)
            self.iface.removeToolBarIcon(action)

    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep
        # reference
        # Only create GUI ONCE in callback, so that it will only load when the
        # plugin is started
        if self.first_start:
            self.first_start = False
            # corresponding dialogs
            self.input_dlg = AnimalMovementAnalysisDialog()
            self.filter_dlg = AnimalMovementAnalysisDialogFilter()
            self.result_dlg = AnimalMovementAnalysisDialogResults()

        # must belong to the instance and be passed across functions
        self.calculos = {}

        # show the first dialog
        self.input_dlg.show()
        # Run the dialog event loop
        upload_result = self.input_dlg.exec_()

        # See if OK was pressed
        if upload_result:
            # get path to the chosen file
            birds_path = self.input_dlg.mQgsFileWidget1.filePath()
            # check if it's a Shapefile
            if not birds_path.endswith('.shp'):
                self.iface.messageBar().pushMessage(
                    "Error", "Please upload a shapefile", level=Qgis.Critical)
            else:
                start = dt.now()
                # load the layer
                birds_layer = QgsVectorLayer(birds_path, "birds layer", "ogr")

                # check if it's a valid Shapefile
                if not birds_layer.isValid():
                    self.iface.messageBar().pushMessage(
                        "Error", "Unfortunately the shapefile could not be \
                        loaded. Please try again with a valid file",
                        level=Qgis.Critical)

                else:
                    # cloning the layer without reference to definitely
                    # not alter the original shapefile
                    birds_layer.selectAll()
                    cloned_layer = processing.run(
                        "native:saveselectedfeatures", {
                            'INPUT': birds_layer,
                            'OUTPUT': 'memory:'})['OUTPUT']

                    """START PREPROCESSING"""

                    # transform to objects for (much) faster computation times
                    birds_object = preproces.constructDataObject(cloned_layer)
                    end1 = dt.now()
                    total_time = end1 - start
                    print("Constructed the whole points object : ", total_time)

                    # remove unnecessary attributes, join tables with the
                    # temperature file
                    all_points = preproces.preprocessing(birds_object)
                    
                    # # add all to the map ?
                    # QgsProject.instance().addMapLayer(cloned_layer)

                    # prepare to find out whether all birds or just 1 have to be analysed
                    # find all unique bird ids in the dataset
                    list_idents = []
                    for point in all_points.values():
                        if (point["ind_ident"] not in list_idents):
                            list_idents.append(point["ind_ident"])
                    list_idents.insert(0, "All")

                    # show the next dialog with bird ids in the comboBox
                    # and seasons in the mComboBox (for multiple choices)
                    self.filter_dlg.show()
                    self.filter_dlg.comboBox.clear()
                    self.filter_dlg.comboBox.addItems(list_idents)
                    self.filter_dlg.comboBox.setCurrentIndex(0)
                    self.filter_dlg.mComboBox.selectAllOptions()
                    self.filter_dlg.button_box.setEnabled(False)

                    # listen to the event on button press, to see if any data was found
                    self.filter_dlg.calculateButton.clicked.connect(
                        lambda: self.calculatePoints(all_points, list_idents))

                    # Run the dialog event loop for filtering
                    filtering_result = self.filter_dlg.exec_()

                    # exists only when data according to the filtering parameters exists
                    if filtering_result:
                        # more time tracking
                        start = dt.now()

                        """ PROCESSING """

                        process_birds = proces.processBird(self.calculos)
                        end1 = dt.now()
                        total_time = end1 - start
                        print("Processed birds ", total_time)

                        # create data for the monthly statistics
                        dist_by_month = proces.monthlyDistanceTemp(
                            process_birds)
                        end2 = dt.now()
                        total_time = end2 - end1
                        print("Did monthly distance temp: ", total_time)

                        # create data for the scatter plot
                        dist_to_scatter = proces.tempAndDist(process_birds)
                        end3 = dt.now()
                        total_time = end3 - end2
                        print("Prepared scatterplot data: ", total_time)

                        # create data for the dist/temp bar charts
                        dist_by_temp = proces.distancePerTemp(process_birds)
                        end4 = dt.now()
                        total_time = end4 - end3
                        print("Prepared data for dist per temp: ", total_time)

                        # show the filtering params from the previous window
                        self.result_dlg.textEdit.setText(
                            '\n'.join(self.selected_birds))
                        self.result_dlg.textEdit_2.setText(
                            '\n'.join(self.selected_seasons))
                        self.result_dlg.show()

                        # listening to button events to display different plots
                        self.result_dlg.distTempButton.clicked.connect(
                            lambda: self.changePlot("temperatures", dist_by_temp))
                        self.result_dlg.monthlyStatsButton.clicked.connect(
                            lambda: self.changePlot("seasons", dist_by_month))
                        self.result_dlg.scatterplotButton.clicked.connect(
                            lambda: self.changePlot("scatter", dist_to_scatter))
                        self.result_dlg.showPlotButton.clicked.connect(
                            lambda: self.changePlot(self.currentPlot, self.currentData, True))

    """
    # Name: calculatePoints(self, all_points, list_idents)
    # Description: function that checks whether there are points to current
    #   filtering parameters. The function alters the self.calculos object,
    #   because .connect() doesn't allow for return values
    # @args:
    #    all_points: the preprocessed points objects, that must be filtered
    #    list_idents: full list of the unique bird ids. 
    """
    def calculatePoints(self, all_points, list_idents):
        print("Search parameters were chosen")
        self.selected_seasons = self.filter_dlg.mComboBox.checkedItems()
        selected_bird_index = self.filter_dlg.comboBox.currentIndex()

        # tracking time again
        start = dt.now()

        if (selected_bird_index == 0):
            # all were selected
            self.selected_birds = list_idents[1:]
        else:
            self.selected_birds = [
                list_idents[selected_bird_index]]

        end1 = dt.now()
        total_time = end1 - start
        print("Set up the filters: ", total_time)

        """START FILTERING"""

        # sort by bird if it's only 1 or just take all of them
        if (len(self.selected_birds) == 1):
            filtered_by_bird = proces.filterDataByBird(
                all_points, self.selected_birds[0])
        else:
            filtered_by_bird = all_points

        # now filter by season or take all if all seasons selected
        if (len(self.selected_seasons) < 4):
            filtered_by_bird_and_season = proces.filterDataBySeason(
                filtered_by_bird, self.selected_seasons)
        else:
            filtered_by_bird_and_season = filtered_by_bird

        end2 = dt.now()
        total_time = end2 - end1
        print("Filtered the points: ", total_time)

        # and now calculate distance flown per bird per day
        self.calculos = proces.calculateDistancePerDay(
            filtered_by_bird_and_season)

        end3 = dt.now()
        total_time = end3 - end2
        print("Distance per day done: ", total_time)

        # disable or enable proceeding according to
        # whether some points were found
        if (not self.calculos):
            self.filter_dlg.lineEdit.setText("No")
            self.filter_dlg.button_box.setEnabled(False)
        else:
            self.filter_dlg.lineEdit.setText("Yes")
            self.filter_dlg.button_box.setEnabled(True)

    """
    # Name: changePlot(self, type, data, popup=False):
    # Description: calls for the plots on button click and
    #   dynamically embeds them into the user interface
    #   or shows them in a popup
    # @args:
    #       type: type of the plot that is being called,
    #             as a String: "temperatures", "seasons",
    #             "scatter"
    #       data: processed dataset that serves as a input
    #       popup: Boolean value to define if embedded or popup
    """
    def changePlot(self, type, data, popup=False):
        # clear the plots just in case
        plt.clf()
        plt.close()
        pixmap = None
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # if it's the temperature/distance boxplots
        if (type == "temperatures"):
            if (popup):
                # just show the popup
                temp_plot.plot(data, False)
            else:
                # or embed it into the interface

                # save values that have to be between functions
                self.currentPlot = "temperatures"
                self.currentData = data
                uri = current_dir + "/temperaturesPlot.png"
                # remove file if it already exists to avoid overlap
                if (os.path.isfile(uri)):
                    os.remove(uri)

                # create the plot and save it
                tempPlot = temp_plot.plot(data, True)
                tempPlot.savefig(uri, bbox_inches='tight')
                # make a QPixmap out of it and load to interface
                pixmap = QPixmap(uri)
                self.result_dlg.statsLabel.setPixmap(pixmap)
                # enable the button that has to be shown full size
                self.result_dlg.showPlotButton.setEnabled(True)

        # same procedure for the monthly statistics
        elif (type == "seasons"):
            if (popup):
                month_plot.plot(data, False)
            else:
                self.currentPlot = "seasons"
                self.currentData = data
                uri = current_dir + "/seasonsPlot.png"
                if (os.path.isfile(uri)):
                    os.remove(uri)

                monthPlot = month_plot.plot(data, True)
                monthPlot.savefig(uri, bbox_inches='tight')
                pixmap = QPixmap(uri)
                self.result_dlg.statsLabel.setPixmap(pixmap)
                self.result_dlg.showPlotButton.setEnabled(True)

        # and for the scatterplot
        else:
            if (popup):
                scatter_plot.scatterPlot(data, False)
            else:
                self.currentPlot = "scatter"
                self.currentData = data
                uri = current_dir + "/scatterPlot.png"
                if (os.path.isfile(uri)):
                    os.remove(uri)

                scatterPlot = scatter_plot.scatterPlot(data, True)
                scatterPlot.savefig(uri, bbox_inches='tight')
                pixmap = QPixmap(uri)
                self.result_dlg.statsLabel.setPixmap(pixmap)
                self.result_dlg.showPlotButton.setEnabled(True)
