from qgis.core import QgsProcessingProvider

from project_checker.algorithms.macros import AreThereMacrosAlgorithm
from project_checker.algorithms.expression_functions import AreThereExpressionFunctionsAlgorithm
from project_checker.algorithms.does_the_project_use_absolute_paths import DoesTheProjectUseAbsolutePathsAlgorithm
from project_checker.algorithms.are_there_custom_project_variables import AreThereCustomProjectVariablesAlgorithm


class ProjectCheckerAlgorithmProvider(QgsProcessingProvider):
    def id(self) -> str:
        return "projectchecker"

    def name(self) -> str:
        return "Project Checker"

    def loadAlgorithms(self):
        self.addAlgorithm(AreThereMacrosAlgorithm())
        self.addAlgorithm(AreThereExpressionFunctionsAlgorithm())
        self.addAlgorithm(DoesTheProjectUseAbsolutePathsAlgorithm())
        self.addAlgorithm(AreThereCustomProjectVariablesAlgorithm())
