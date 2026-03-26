from typing import Any, Optional

from qgis.core import (
    Qgis,
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProcessingOutputBoolean,
    QgsProcessingOutputVariant,
    QgsProcessingParameterFile,
    QgsVectorLayer,
)

from project_checker.misc import project_from_file_or_running_qgis


class AreVectorLayersMissingSpatialIndexesAlgorithm(QgsProcessingAlgorithm):
    PROJECT = "PROJECT"
    VERDICT = "VERDICT"
    DETAILS = "DETAILS"

    def name(self) -> str:
        return "missingspatialindexes"

    def displayName(self) -> str:
        return "Missing Spatial Indexes"

    def group(self) -> str:
        return "Layer Checks"

    def groupId(self) -> str:
        return "layerchecks"

    def shortHelpString(self) -> str:
        return (
            "Checks all vector layers in the project for spatial indexes. "
            "Returns a list of layers that are missing a spatial index."
        )

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

        layers_missing_index = []
        for layer in project.mapLayers().values():
            if feedback.isCanceled():
                break
            if not isinstance(layer, QgsVectorLayer):
                continue
            if layer.hasSpatialIndex() == Qgis.SpatialIndexPresence.NotPresent:
                feedback.pushInfo(f"Layer '{layer.name()}' is missing a spatial index.")
                layers_missing_index.append(layer.id())

        feedback.pushInfo(
            f"{len(layers_missing_index)} layer(s) missing spatial indexes."
        )
        return {
            self.VERDICT: bool(layers_missing_index),
            self.DETAILS: layers_missing_index,
        }

    @classmethod
    def createInstance(cls):
        return cls()