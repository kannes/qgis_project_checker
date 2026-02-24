from typing import Optional

from qgis.core import QgsApplication, QgsProcessingProvider
from qgis.gui import QgisInterface

from project_checker.processing_provider import ProjectCheckerAlgorithmProvider

iface: QgisInterface


class ProjectCheckerPlugin:
    def __init__(self):
        self.provider: Optional[QgsProcessingProvider] = None

    def initGui(self):
        self.provider = ProjectCheckerAlgorithmProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)
