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


class AreThereCustomProjectVariablesAlgorithm(QgsProcessingAlgorithm):
    PROJECT = "PROJECT"
    VERDICT = "VERDICT"
    DETAILS = "DETAILS"

    def name(self) -> str:
        return "customprojectvariables"

    def displayName(self) -> str:
        return "Custom Project Variables"

    def group(self) -> str:
        return "Project Settings"

    def groupId(self) -> str:
        return "projectsettings"

    def shortHelpString(self) -> str:
        return "Checks if the project has custom variables (not layer variables)."

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

        custom_variables = project.customVariables()
        if bool(custom_variables):
            feedback.pushInfo("Project has custom variables.")
            return {self.VERDICT: True, self.DETAILS: custom_variables}
        else:
            feedback.pushInfo("Project does not have custom variables.")
            return {self.VERDICT: False, self.DETAILS: None}

    @classmethod
    def createInstance(cls):
        return cls()
