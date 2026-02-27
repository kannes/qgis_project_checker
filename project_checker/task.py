import logging

from typing import Any, NamedTuple, Optional

from qgis.PyQt.QtCore import QObject, pyqtSignal
from qgis.core import QgsProcessingFeedback, QgsProcessingContext

import processing

CheckerResult = NamedTuple("CheckerResult", [("algorithm_id", str), ("verdict", bool), ("details", Any)])


# task so we can nicely update the GUI without blocking or what?
class Task(QObject):
    runFinished = pyqtSignal(tuple, name="runFinished")

    def __init__(
        self,
        algorithm_id: str,
        parameters: dict[str, Any],
        parent: Optional[QObject] = None,
    ):
        """TODO

        Args:
             algorithm_id: E.g. "projectchecker:foo"
             parameters: E.g. {"INPUT": True, "OUTPUT": QgsProcessing.TEMPORARY_OUTPUT}
             TODO
        """
        super().__init__(parent=parent)

        self.__algorithm_id = algorithm_id
        self.__parameters = parameters

    def __execute_algorithm(self) -> CheckerResult:
        logging.debug(f"Executing {self.__algorithm_id!s} with {self.__parameters!r}")
        algorithm_results = processing.run(self.__algorithm_id, self.__parameters)
        logging.debug(f"{algorithm_results=}")
        checker_result = CheckerResult(self.__algorithm_id, algorithm_results["VERDICT"], algorithm_results["DETAILS"])
        return checker_result

    def run(self) -> None:
        checker_result = self.__execute_algorithm()
        self.runFinished.emit(checker_result)
