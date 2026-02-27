from typing import Any, Optional

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProcessingOutputBoolean,
    QgsProcessingOutputVariant,
    QgsProcessingParameterFile,
)

from project_checker.misc import project_from_file_or_running_qgis


class DoesTheProjectUseAbsolutePathsAlgorithm(QgsProcessingAlgorithm):
    PROJECT = "PROJECT"
    VERDICT = "VERDICT"
    DETAILS = "DETAILS"

    def name(self) -> str:
        return "absolutepaths"

    def displayName(self) -> str:
        return "Absolute Paths"

    def group(self) -> str:
        return "Project Settings"

    def groupId(self) -> str:
        return "projectsettings"

    def shortHelpString(self) -> str:
        return "Checks if the project uses absolute paths."

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
        self.addOutput(QgsProcessingOutputVariant(self.DETAILS, "Details"))

    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: Optional["QgsProcessingFeedback"],
    ) -> dict[str, Any]:
        file_path = self.parameterAsFile(parameters, self.PROJECT, context)
        project = project_from_file_or_running_qgis(file_path, feedback)

        absolute_paths, _ = project.readEntry("Paths", "/Absolute")
        if bool(absolute_paths):
            feedback.pushInfo("Project uses absolute paths.")
            return {self.VERDICT: True, self.DETAILS: None}
        else:
            feedback.pushInfo("Project does not use absolute paths.")
            return {self.VERDICT: False, self.DETAILS: None}

    @classmethod
    def createInstance(cls):
        return cls()
