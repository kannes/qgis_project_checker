from typing import Any, Optional

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProcessingOutputVariant,
    QgsProcessingParameterBoolean,
    QgsProject,
)


class CheckForExpressionFunctionsAlgorithm(QgsProcessingAlgorithm):
    INPUT = "INPUT"
    OUTPUT = "OUTPUT"

    def name(self) -> str:
        return "expressionfunctions"

    def displayName(self) -> str:
        return "Expression Functions"

    def group(self) -> str:
        return "Executable Code"

    def groupId(self) -> str:
        return "executablecode"

    def shortHelpString(self) -> str:
        return "Checks if the project contains expression functions"

    def initAlgorithm(self, config: Optional[dict[str, Any]] = None):
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.INPUT, "A parameter is needed or we get no dialog from QGIS", optional=True
            )
        )
        self.addOutput(QgsProcessingOutputVariant(self.OUTPUT, "Output"))

    def processAlgorithm(
        self, parameters: dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> dict[str, Any]:
        expression_functions: str
        expression_functions, _ = QgsProject.instance().readEntry("ExpressionFunctions", "/pythonCode")
        if expression_functions:
            feedback.pushInfo("Expression functions found.")
            return {self.OUTPUT: expression_functions}
        else:
            feedback.pushInfo("No expression functions found.")
            return {}

    @classmethod
    def createInstance(cls):
        return cls()
