from typing import Any, Optional

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProcessingOutputVariant,
    QgsProcessingParameterBoolean,
    QgsProject,
)


class CheckForMacrosAlgorithm(QgsProcessingAlgorithm):
    INPUT = "INPUT"
    OUTPUT = "OUTPUT"

    def name(self) -> str:
        return "macros"

    def displayName(self) -> str:
        return "Macros"

    def group(self) -> str:
        return "Executable Code"

    def groupId(self) -> str:
        return "executablecode"

    def shortHelpString(self) -> str:
        return "Checks if the project contains macros (embedded Python code)"

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
        macros: str
        macros, _ = QgsProject.instance().readEntry("Macros", "/pythonCode")
        if macros:
            feedback.pushInfo("Macro(s) found.")
            return {self.OUTPUT: macros}
        else:
            feedback.pushInfo("No macros found.")
            return {}

    @classmethod
    def createInstance(cls):
        return cls()
