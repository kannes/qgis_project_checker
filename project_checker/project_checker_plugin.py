import logging

from typing import Optional

from qgis.PyQt.QtGui import QAction

from qgis.core import QgsApplication, QgsProcessingProvider
from qgis.gui import QgisInterface
from qgis.utils import iface

from project_checker.processing_provider import ProjectCheckerAlgorithmProvider
from project_checker.wizard import ProjectCheckerWizard

iface: QgisInterface

logging.basicConfig(
    format="%(asctime)s %(levelname)s:%(message)s",
    level=logging.DEBUG,
    datefmt="%Y-%m-%d %H:%M:%S",
)


class ProjectCheckerPlugin:
    def __init__(self):
        self.provider: Optional[QgsProcessingProvider] = None

    def initGui(self):
        self.provider = ProjectCheckerAlgorithmProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

        self.wizard_action = QAction("Project Checker Wizard")
        self.wizard_action.triggered.connect(self.__summon_wizard)
        iface.addToolBarIcon(self.wizard_action)

    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)

        iface.removeToolBarIcon(self.wizard_action)
        del self.wizard_action

    def __summon_wizard(self):
        wizard = ProjectCheckerWizard(parent=iface.mainWindow())  # TODO parent ok?
        wizard.exec()
