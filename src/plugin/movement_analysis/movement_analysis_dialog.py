# -*- coding: utf-8 -*-
"""
/***************************************************************************
 AnimalMovementAnalysisDialog
                                 A QGIS plugin
 This plugin finds correlation between air temperature and activity patterns of animals chosen by the user in the area of North Rhine-Westphalia
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2019-06-23
        git sha              : $Format:%H$
        copyright            : (C) 2019 by Aditya Rajendra Kudekar, Violeta Ana Luz Sosa León, Tina Baidar, Muhammad Saad Saif, Anna Formaniuk
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

import os

from PyQt5 import uic
from PyQt5 import QtWidgets

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'movement_analysis_dialog_base.ui'))


class AnimalMovementAnalysisDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(AnimalMovementAnalysisDialog, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)