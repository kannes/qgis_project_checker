from contextlib import contextmanager

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QApplication

from qgis.core import (
    QgsApplication,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingFeedback,
    QgsProcessingProvider,
    QgsProject,
)


@contextmanager
def wait_cursor():
    try:
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        yield
    except Exception as ex:
        raise ex
    finally:
        QApplication.restoreOverrideCursor()


def available_algorithms() -> list[QgsProcessingAlgorithm]:
    provider: QgsProcessingProvider = QgsApplication.processingRegistry().providerById("projectchecker")
    return provider.algorithms()


def project_from_file_or_running_qgis(file_path: str, feedback: QgsProcessingFeedback):
    """TODO

    Raises:
         QgsProcessingException: If no QgsProject could be read from the passed file
    """
    # TODO less verbose feedback?
    feedback.pushInfo(f"{file_path=}")
    if file_path:
        feedback.pushInfo(f"Trying to read {file_path!s}")
        project = QgsProject()
        read_success = project.read(file_path)
        if not read_success:
            raise QgsProcessingException("Provided project file could not be read")
    else:
        feedback.pushInfo("Using currently opened QGIS project")
        project = QgsProject.instance()
    feedback.pushInfo(f"Checking {project.fileName()!s}")
    return project
