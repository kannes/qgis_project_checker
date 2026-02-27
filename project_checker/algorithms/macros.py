from typing import Any, Optional

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProcessingOutputBoolean,
    QgsProcessingOutputString,
    QgsProcessingParameterFile,
)

from project_checker.misc import project_from_file_or_running_qgis


class AreThereMacrosAlgorithm(QgsProcessingAlgorithm):
    PROJECT = "PROJECT"
    VERDICT = "VERDICT"
    DETAILS = "DETAILS"

    def name(self) -> str:
        return "macros"

    def displayName(self) -> str:
        return "Macros"

    def group(self) -> str:
        return "Executable Code"

    def groupId(self) -> str:
        return "executablecode"

    def shortHelpString(self) -> str:
        return "Checks if the project contains macros (embedded Python code). If so, returns them as string."

    def initAlgorithm(self, config: Optional[dict[str, Any]] = None):
        self.addParameter(
            QgsProcessingParameterFile(
                self.PROJECT,
                "QGIS project file to check. If not set, the currently opened project will be checked",
                optional=True,
                fileFilter="Project Files (*.qgs *.qgz)",
            )
        )
        self.addOutput(QgsProcessingOutputBoolean(self.VERDICT, "Verdict"))
        self.addOutput(QgsProcessingOutputString(self.DETAILS, "Details"))

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: Optional["QgsProcessingFeedback"],
    ) -> dict[str, Any]:
        file_path = self.parameterAsFile(parameters, self.PROJECT, context)
        project = project_from_file_or_running_qgis(file_path, feedback)

        macros, _ = project.readEntry("Macros", "/pythonCode")
        if macros:
            feedback.pushInfo("Macro(s) found.")
            return {self.VERDICT: True, self.DETAILS: macros}
        else:
            feedback.pushInfo("No macros found.")
            return {self.VERDICT: False, self.DETAILS: None}

    @classmethod
    def createInstance(cls):
        return cls()
