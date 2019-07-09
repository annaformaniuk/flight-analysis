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
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .movement_analysis_dialog import (AnimalMovementAnalysisDialog,
                                       AnimalMovementAnalysisDialogFilter)
# import os.path
from qgis.core import (QgsProject, QgsColorRampShader,
                       Qgis, QgsVectorLayer, QgsRasterLayer,
                       QgsSingleBandPseudoColorRenderer,
                       QgsVectorDataProvider, QgsField)

from datetime import datetime as dt

# from qgis.core import *
import qgis.utils
import os

# import local processing files
sys.path.insert(0, './preprocessing')
sys.path.insert(0, './processing')
try:
    from .preprocessing import preprocessing_new as ppn
    from .processing import processing_analysis as pa
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
        self.calculos = {}
        if self.first_start:
            self.first_start = False
            self.dlg1 = AnimalMovementAnalysisDialog()
            self.dlg2 = AnimalMovementAnalysisDialogFilter()

        # show the dialog
        self.dlg1.show()
        # Run the dialog event loop
        upload_result = self.dlg1.exec_()
        # self.dlg1.mQgsFileWidget1.clear()
        # See if OK was pressed
        if upload_result:
            # get paths to the chosen files
            birds_path = self.dlg1.mQgsFileWidget1.filePath()
            # check if it's a Shapefile
            if not birds_path.endswith('.shp'):
                self.iface.messageBar().pushMessage(
                    "Error", "Please upload shapefile", level=Qgis.Critical)

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
                    # cloning the layer without reference not to alter
                    # the original file
                    birds_layer.selectAll()
                    cloned_layer = processing.run(
                        "native:saveselectedfeatures", {
                            'INPUT': birds_layer,
                            'OUTPUT': 'memory:'})['OUTPUT']

                    # remove unnecessary attributes, join tables with the
                    # temperature file
                    birds_object = ppn.constructDataObject(cloned_layer)
                    end1 = dt.now()
                    total_time = end1 - start
                    print("Constructed the whole object : ", total_time)
                    all_points = ppn.preprocessing(birds_object)
                    print("Preprocessed")
                    # # add all to the map
                    # QgsProject.instance().addMapLayer(cloned_layer)

                    # find out whether all birds or just 1 have to be analysed
                    # features = cloned_layer.getFeatures()
                    # ind_idents = {feature["ind_ident"] for feature in all_points}
                    list_idents = []
                    for point in all_points.values():
                        if (point["ind_ident"] not in list_idents):
                            list_idents.append(point["ind_ident"])
                    # list_idents = list(ind_idents)
                    list_idents.insert(0, "All")

                    # show the next dialog
                    self.dlg2.show()
                    self.dlg2.comboBox.clear()
                    self.dlg2.comboBox.addItems(list_idents)
                    self.dlg2.comboBox.setCurrentIndex(0)
                    self.dlg2.mComboBox.selectAllOptions()
                    self.dlg2.button_box.setEnabled(False)

                    def calculatePoints():
                        print("Something was chosen")
                        selected_seasons = self.dlg2.mComboBox.checkedItems()
                        selected_bird_index = self.dlg2.comboBox.currentIndex()

                        if (selected_bird_index == 0):
                            selected_birds = list_idents[1:]
                        else:
                            selected_birds = [list_idents[selected_bird_index]]

                        print(selected_seasons, selected_birds)

                        # construct the data_object required in the processing
                        # all_points = pa.constructDataObject(cloned_layer)

                        # sort by bird if it's only 1 or just take all of them
                        if (len(selected_birds) == 1):
                            filtered_by_bird = pa.filterDataByBird(
                                all_points, selected_birds[0])
                        else:
                            filtered_by_bird = all_points

                        # now filter by season
                        filtered_by_bird_and_season = pa.filterDataBySeason(
                            filtered_by_bird, selected_seasons)

                        # and now calculate distance per day
                        self.calculos = pa.calculateDistancePerDay(
                            filtered_by_bird_and_season)

                        if (len(self.calculos) == 0):
                            self.dlg2.lineEdit.setText("0")
                            self.dlg2.button_box.setEnabled(False)
                        else:
                            points_amount = 0
                            for obj in self.calculos.values():
                                points_amount += len(obj)
                            self.dlg2.lineEdit.setText(str(points_amount))
                            self.dlg2.button_box.setEnabled(True)

                    self.dlg2.calculateButton.clicked.connect(
                        lambda: calculatePoints())

                    # Run the dialog event loop
                    filtering_result = self.dlg2.exec_()

                    if filtering_result:
                        print("Yay")
