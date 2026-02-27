from typing import Any, Dict, List, Optional

from qgis.core import (
    QgsMapLayerType,  # Enum for QGIS layer types (Vector, Raster, Mesh, etc.)
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingFeedback,
    QgsProcessingOutputVariant,
    QgsProcessingParameterBoolean,
    QgsProject,
)


def _layer_type_label(layer) -> str:
    """
    Convert a QGIS layer type to a human-readable string label.
    
    This function is version-safe across different QGIS releases by using
    getattr() with fallbacks to handle layers not available in all versions.
    
    Args:
        layer: A QGIS map layer object.
        
    Returns:
        A string label (e.g., "vector", "raster", "mesh") or "unknown" as fallback.
    """
    t = layer.type()

    """Map QGIS layer type enums to human-readable labels using getattr() for graceful handling"""
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

    label = mapping.get(t)
    if label:
        return label

    """Fallback strategy: attempt to extract the enum name, or use numeric value as last resort"""
    try:
        return getattr(t, "name", None) or f"unknown({int(t)})"
    except Exception:
        return "unknown"


class CheckForLayerCrsMismatchesAlgorithm(QgsProcessingAlgorithm):
    """
    Processing algorithm that detects CRS (Coordinate Reference System) mismatches
    between project layers and the project's defined CRS.
    
    This algorithm:
    1. Reads the project's CRS AuthID (e.g., "EPSG:4326")
    2. Iterates through all map layers
    3. Identifies layers whose CRS AuthID differs from the project CRS
    4. Flags layers using custom CRS without a standard AuthID
    5. Returns detailed mismatch and warning information
    """

    """Input/Output slot names for QGIS processing framework"""
    INPUT = "INPUT"
    OUTPUT = "OUTPUT"

    def name(self) -> str:
        """
        Return the algorithm's internal identifier (used by QGIS Processing).
        This name must be unique and lowercase with underscores.
        """
        return "check_layer_crs_mismatches"

    def displayName(self) -> str:
        """Return the algorithm's user-friendly name shown in the Processing Toolbox."""
        return "Check layer CRS mismatches"

    def group(self) -> str:
        """Return the category/group name for organizing algorithms in the Toolbox."""
        return "Executable Code"

    def groupId(self) -> str:
        """
        Return the internal group identifier (lowercase, underscores).
        Used for organizing algorithms hierarchically in the Toolbox UI.
        """
        return "executablecode"

    def shortHelpString(self) -> str:
        """Return a brief help text displayed in the algorithm's Help panel."""
        return "Finds project layers whose CRS AuthID mismatches with the project CRS AuthID."

    def initAlgorithm(self, config: Optional[Dict[str, Any]] = None):
        """
        Configure the algorithm's input parameters and output.
        
        A dummy Boolean parameter is added because QGIS requires at least one
        parameter to display the algorithm's dialog box properly.
        """
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.INPUT, "A parameter is needed or we get no dialog from QGIS", optional=True, defaultValue=True,
            )
        )
        self.addOutput(QgsProcessingOutputVariant(self.OUTPUT, "Output"))

    def processAlgorithm(
        self, parameters: Dict[str, Any], context: QgsProcessingContext, feedback: QgsProcessingFeedback
    ) -> Dict[str, Any]:
        """
        Main algorithm execution logic.
        
        Analyzes the project's CRS and compares it against each layer's CRS.
        Collects two result sets:
        - Mismatches: layers with a valid AuthID that differs from project CRS
        - Custom CRS warnings: layers using custom CRS without a standard AuthID
        
        Returns detailed information about each issue via feedback messages and output dict.
        """
        """Fetch the active QGIS project and its configured CRS"""
        project = QgsProject.instance()
        project_crs = project.crs()
        """Extract the AuthID (e.g., EPSG:4326); empty string if CRS is invalid"""
        project_authid = project_crs.authid() if project_crs.isValid() else ""

        """Initialize result lists"""
        mismatches: List[Dict[str, Any]] = []
        custom_crs_warnings: List[Dict[str, Any]] = []

        def build_layer_info(layer, layer_authid: str) -> Dict[str, Any]:
            """
            Create a standardized dictionary with layer metadata.
            
            Args:
                layer: The QGIS map layer object.
                layer_authid: The layer's CRS AuthID string.
                
            Returns:
                Dictionary containing layer ID, name, type label, and AuthID.
            """
            return {
                "layerId": layer.id(),
                "layerName": layer.name(),
                "layerType": _layer_type_label(layer),
                "layerAuthId": layer_authid,
            }

        """Iterate through all project layers"""
        for layer in project.mapLayers().values():
            """Skip layers that don't have a CRS (e.g., annotation layers, group layers)"""
            if not hasattr(layer, "crs"):
                continue

            layer_crs = layer.crs()
            """Skip layers with invalid/undefined CRS"""
            if not layer_crs.isValid():
                continue

            """Retrieve the layer's CRS AuthID"""
            layer_authid = layer_crs.authid()
            layer_info = build_layer_info(layer, layer_authid)

            """Retrieve the layer's CRS AuthID"""
            layer_info = build_layer_info(layer, layer_authid)

            """Check if layer uses custom CRS (no standard AuthID)"""
            if not layer_authid:
                custom_crs_warnings.append(
                    {
                        "layerId": layer.id(),
                        "layerName": layer.name(),
                        "layerType": _layer_type_label(layer),
                        "layerCrsDescription": layer_crs.description(),
                    }
                )
                continue

            """Check if layer's AuthID differs from project's AuthID"""
            if project_authid and layer_authid != project_authid:
                mismatches.append(layer_info)

        """Assemble final result dictionary for output"""
        result: Dict[str, Any] = {
            "projectAuthId": project_authid,
            "mismatches": mismatches,
            "customCrsWarnings": custom_crs_warnings,
        }

        """Inform user of the project's CRS"""
        feedback.pushInfo(f"Project CRS AuthID: {project_authid or '(none)'}")

        """Report results: either all clear or detailed mismatch/warning list"""
        if not mismatches and not custom_crs_warnings:
            feedback.pushInfo("No CRS issues found.")
        else:
            """Report CRS AuthID mismatches with detailed layer information"""
            if mismatches:
                feedback.pushWarning(f"CRS mismatches found ({len(mismatches)}):")
                for m in mismatches:
                    feedback.pushInfo(
                        f"  - {m['layerName']} [{m['layerType']}] : {m['layerAuthId']} (project: {project_authid})"
                    )

            """Report layers using custom CRS without standard AuthID"""
            if custom_crs_warnings:
                feedback.pushWarning(f"Layers with custom CRS / missing AuthID found: ({len(custom_crs_warnings)}):")
                for w in custom_crs_warnings:
                    feedback.pushInfo(
                        f"  - {w['layerName']} [{w['layerType']}] : {w.get('layerCrsDescription', '(no description)')}"
                    )

        return {self.OUTPUT: result}

    @classmethod
    def createInstance(cls):
        """
        Factory method required by QGIS Processing framework.
        Returns a new instance of this algorithm.
        """
        return cls()