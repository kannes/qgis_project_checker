from qgis.core import QgsProcessingProvider

from project_checker.algorithms.macros import AreThereMacrosAlgorithm
from project_checker.algorithms.expression_functions import AreThereExpressionFunctionsAlgorithm


class ProjectCheckerAlgorithmProvider(QgsProcessingProvider):
    def id(self) -> str:
        return "projectchecker"

    def name(self) -> str:
        return "Project Checker"

    def loadAlgorithms(self):
        self.addAlgorithm(AreThereMacrosAlgorithm())
        self.addAlgorithm(AreThereExpressionFunctionsAlgorithm())
