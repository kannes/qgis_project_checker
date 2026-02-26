from typing import Any, Optional

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProcessingOutputVariant,
    QgsProcessingParameterBoolean,
    QgsProject,
)

"""
This class inherits from the parent class (QgsProcessingAlgorithm):
"""
class CheckForCrsAlgorithm(QgsProcessingAlgorithm):
    """
    It checks with an algorithm if the current QGIS project is using a CRS.
    If yes, it returns a dictionary, with the CRS details.
    If Not, it returns "".
    """

    INPUT = "INPUT"
    OUTPUT = "OUTPUT"

    def name(self) -> str:
        return "check_project_crs"      # returns internal ID of the Processing Algorithm

    def displayName(self) -> str:
        return "Check Project CRS"      # returns display name

    def group(self) -> str:
        return "Executable Code"        # returns Group- / Folder -name

    def groupId(self) -> str:
        return "executablecode"         # returns internal ID of the Group, to find the algorithm
                                        # in the Processing Toolbox

    def shortHelpString(self) -> str:
        return (
            "Checks whether the current QGIS project is using a CRS."   # returns information for User
        )
    """
    This function defines the "dialogue", inputs and outputs of the Processing - Tool
    """
    def initAlgorithm(self, config: Optional[dict[str, Any]] = None):
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.INPUT, "A parameter is needed or we get no dialog from QGIS", optional=True, defaultValue=True,
            )
        )
        self.addOutput(QgsProcessingOutputVariant(self.OUTPUT, "Output"))

    """
    Function "processAlgorithm"
    """
    def processAlgorithm(
        self,
        parameters: dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> dict[str, Any]:
        project = QgsProject.instance()     # "take the project, currently opened in QGIS"
        crs = project.crs()                 # "read the project-CRS of the opened project"

        authid = crs.authid() if crs.isValid() else ""      # "If CSR is valid, take authid. If not, set authid as ""

        # Requirement: only count as "KBS used" if authid is non-empty (e.g. EPSG:xxxx)
        if authid:                                  # If authid is not empty the authid is used to build a dictionary:
            result: dict[str, Any] = {
                "authid": authid,
                "description": crs.description(),
                "projectionAcronym": crs.projectionAcronym(),
                "ellipsoidAcronym": crs.ellipsoidAcronym(),
                "isGeographic": crs.isGeographic(),
            }
            feedback.pushInfo(f"Project CRS (KBS) found: {authid}")     # returns the project CRS
            return {self.OUTPUT: result}

        feedback.pushInfo('No project CRS (KBS) with AuthID (e.g. "EPSG:xxxx") found.')
        return {self.OUTPUT: ""}

    @classmethod
    def createInstance(cls):
        return cls()
