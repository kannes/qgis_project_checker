from typing import Any, Dict, List, Optional

from qgis.core import (
    QgsMapLayerType,
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
class CheckForLayerDataTypes(QgsProcessingAlgorithm):
    """
    Lists all project layers with datatype and CRS match / mismatch status.
    """

    INPUT = "INPUT"
    OUTPUT = "OUTPUT"

    def name(self) -> str:
        return "list_layer_datatypes"

    def displayName(self) -> str:
        return "Layer List with Datatypes and CRS check"

    def group(self) -> str:
        return "Executable Code"

    def groupId(self) -> str:
        return "executablecode"

    def shortHelpString(self) -> str:
        return "Lists all layers with datatype and CRS match / mismatch status."

    """
    This function defines the "dialogue", inputs and outputs of the Processing - Tool
    """
    def initAlgorithm(self, config: Optional[Dict[str, Any]] = None):
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
        parameters: Dict[str, Any],
        context: QgsProcessingContext,
        feedback: QgsProcessingFeedback,
    ) -> Dict[str, Any]:
        project = QgsProject.instance()
        project_crs = project.crs()
        project_authid = project_crs.authid() if project_crs.isValid() else ""

        def layer_type_label(layer) -> str:
            mapping = {
                getattr(QgsMapLayerType, "VectorLayer", None): "vector",
                getattr(QgsMapLayerType, "RasterLayer", None): "raster",
                getattr(QgsMapLayerType, "PluginLayer", None): "plugin",
                getattr(QgsMapLayerType, "MeshLayer", None): "mesh",
                getattr(QgsMapLayerType, "VectorTileLayer", None): "vector-tile",
                getattr(QgsMapLayerType, "PointCloudLayer", None): "point-cloud",
                getattr(QgsMapLayerType, "TiledSceneLayer", None): "tiled-scene",
                getattr(QgsMapLayerType, "AnnotationLayer", None): "annotation",
                getattr(QgsMapLayerType, "GroupLayer", None): "group",
            }
            label = mapping.get(layer.type())
            return label or "unknown"

        def geometry_type_label(layer) -> str:
            if not hasattr(layer, "geometryType"):
                return ""
            geometry_map = {
                0: "Point",
                1: "Line",
                2: "Polygon",
            }
            try:
                return geometry_map.get(layer.geometryType(), "Unknown")
            except Exception:
                return ""

        all_layers: List[Dict[str, Any]] = []

        for layer in project.mapLayers().values():
            layer_type = layer_type_label(layer)
            geom_type = geometry_type_label(layer)
            data_type = f"{layer_type} ({geom_type})" if geom_type else layer_type

            layer_crs = layer.crs() if hasattr(layer, "crs") else None
            layer_authid = layer_crs.authid() if layer_crs and layer_crs.isValid() else ""

            if not layer_crs or not layer_crs.isValid():
                crs_status = "no CRS"
            elif not layer_authid:
                crs_status = "custom CRS"
            elif not project_authid:
                crs_status = "unknown"
            elif layer_authid == project_authid:
                crs_status = "match"
            else:
                crs_status = "mismatch"

            all_layers.append(
                {
                    "layerId": layer.id(),
                    "layerName": layer.name(),
                    "layerType": layer_type,
                    "geometryType": geom_type,
                    "dataType": data_type,
                    "layerAuthId": layer_authid,
                    "crsStatus": crs_status,
                }
            )

        result: Dict[str, Any] = {
            "projectAuthId": project_authid,
            "allLayers": all_layers,
        }

        feedback.pushInfo(f"Project CRS AuthID: {project_authid or '(none)'}")
        feedback.pushInfo(f"Total layers in project: {len(all_layers)}")

        if all_layers:
            feedback.pushInfo("\n=== All Project Layers ===")
            for lyr in all_layers:
                feedback.pushInfo(
                    f"  - {lyr['layerName']} [{lyr['dataType']}] : "
                    f"{lyr['layerAuthId'] or '(no CRS)'} - {lyr['crsStatus']}"
                )

        return {self.OUTPUT: result}

    @classmethod
    def createInstance(cls):
        return cls()