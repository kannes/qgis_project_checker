from qgis.core import QgsProcessingProvider

from project_checker.algorithms.macros import CheckForMacrosAlgorithm
from project_checker.algorithms.expression_functions import CheckForExpressionFunctionsAlgorithm
from project_checker.algorithms.crs import CheckForCrsAlgorithm
from project_checker.algorithms.crs_layer_check import CheckForLayerCrsMismatchesAlgorithm
from project_checker.algorithms.layer_list import CheckForLayerDataTypes


class ProjectCheckerAlgorithmProvider(QgsProcessingProvider):
    def id(self) -> str:
        return "projectchecker"

    def name(self) -> str:
        return "Layer Data CRS"

    def loadAlgorithms(self):
        self.addAlgorithm(CheckForMacrosAlgorithm())
        self.addAlgorithm(CheckForExpressionFunctionsAlgorithm())
        self.addAlgorithm(CheckForCrsAlgorithm())
        self.addAlgorithm(CheckForLayerCrsMismatchesAlgorithm())
        self.addAlgorithm(CheckForLayerDataTypes())