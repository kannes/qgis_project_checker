# Project Checker
 A QGIS plugin to check QGIS projects for potential issues.

# This and that
- Each check must be implemented as `QgsProcessingAlgorithm`.
- Checks must be thread-safe. They might run on the current `QgsProject.instance()`.
- Checks must be named as a question "if a problem exists". E.g. "`DoProblemsExist`" or "`AreThereIssues`".
- Each check must accept at least a `QgsProject` as input (which may be `None`): `{"INPUT": QgsProject}`
- Each check must return a dictionary: `{"VERDICT": bool, "DETAILS": Any}`
- The GUI currently executes the algorithms without `QgsProcessingContext`!

# Ideas for improvements
- Show the `QgsProcessingFeedback` in the GUI for each chosen check (in the `AlgorithmResultWidget`?)
- Add more checks, see below
- Write unittests
- Allow the user to configure input parameters for algorithms in the GUI (e.g. a CRS, a list of CRS, layers, ...)
- Add algorithms that can (try to) fix specific issues, add functions that can (try to) fix issues outside the scope of
  QgsProcessingAlgorithms
- Design a nice logo
- ...

# Ideas for checks
- `IsProjectCrsInvalid`
- `IsProjectCrsNotInWhitelist` -> `QgsCoordinateReferenceSystem`
- `AreVectorLayersMissingSpatialIndexes` -> list of `QgsVectorLayer`s
- `AreRasterLayersMissingOverviews` -> list of `QgsRasterLayer`s
- `AreLayersUsingSlowFormats` -> list of `QgsMapLayer`s and their formats
- ...