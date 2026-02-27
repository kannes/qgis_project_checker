import logging

from typing import Any, Optional

from qgis.PyQt.QtCore import QObject, Qt
from qgis.PyQt.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QWizard,
    QWizardPage,
)

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProject,
)

import processing

from project_checker.misc import available_algorithms, wait_cursor
from project_checker.task import CheckerResult, Task


class AlgorithmInfoWidget(QWidget):
    def __init__(self, algorithm: Optional[QgsProcessingAlgorithm] = None, parent: Optional[QObject] = None) -> None:
        super().__init__(parent=parent)

        layout = QVBoxLayout(self)
        self.__name_label = QLabel("", self)
        self.__name_label.setStyleSheet("font-weight: bold;")
        self.__description_label = QLabel("", self)
        self.__description_label.setWordWrap(True)

        self.setMinimumWidth(200)
        self.setMaximumWidth(200)

        layout.addWidget(self.__name_label)
        layout.addWidget(self.__description_label)
        layout.addStretch(True)

        if algorithm:
            self.set_algorithm(algorithm)

    def set_algorithm(self, algorithm: QgsProcessingAlgorithm) -> None:
        self.__name_label.setText(algorithm.displayName())
        self.__description_label.setText(algorithm.shortHelpString())

    # TODO let the user configure the algorithm here?


class ProjectCheckerWizard(QWizard):

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.setWindowTitle("Project Checker Wizard")

        self.selected_algorithms: list[QgsProcessingAlgorithm] = []
        self.selected_project: QgsProject = None  # None means -> use QgsProject.instance()

        # register pages, automatically sets the QWizard as parent
        self.addPage(SelectProjectPage())
        self.addPage(SelectChecksPage())
        self.addPage(ChecksResultsPage())


class SelectProjectPage(QWizardPage):

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.setTitle("Select QGIS Project")
        self.setSubTitle("Select QGIS project to run check on")

        self.__file_lineedit = QLineEdit(self)
        self.__file_lineedit.setClearButtonEnabled(True)
        self.__file_lineedit.textChanged.connect(self.__update_selected_project)

        file_button = QPushButton("...")
        file_button.clicked.connect(self.__get_file_name)

        layout = QHBoxLayout(self)
        layout.addWidget(QLabel("QGIS project", self))
        layout.addWidget(self.__file_lineedit)
        layout.addWidget(file_button)

    def __get_file_name(self):
        project_file, _ = QFileDialog.getOpenFileName(
            self, caption="Choose QGIS Project", filter="QGIS Projects (*.qgs *.qgz);;All Files (*)"
        )
        self.__file_lineedit.setText(project_file)

    def __update_selected_project(self):
        file_path = self.__file_lineedit.text().strip()
        if file_path:  # catch empty string
            self.wizard().selected_project = file_path
        # TODO save selected project in QgsSettings?


class SelectChecksPage(QWizardPage):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent)

        self.setTitle("Select Checks")
        self.setSubTitle("Select checks to execute on the current QGIS project")

        self.__algorithm_list = QListWidget(self)
        self.__algorithm_helptext = AlgorithmInfoWidget(parent=self)

        layout = QGridLayout(self)
        layout.addWidget(self.__algorithm_list, 0, 0)
        layout.addWidget(self.__algorithm_helptext, 0, 1)

        for i, algorithm in enumerate(available_algorithms()):
            item = QListWidgetItem(self.__algorithm_list)
            item.setText(algorithm.displayName())
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            item.setIcon(algorithm.icon())
            item.setToolTip(algorithm.shortHelpString())
            item.setData(Qt.ItemDataRole.UserRole, algorithm)  # yolo! less work than using a model ;D
            self.__algorithm_list.insertItem(i, item)

        self.__algorithm_list.currentItemChanged.connect(self.__update_algorithm_helptext)

        # there is no explicit signal for qlwitems checkboxes so we cannot react on a single checkbox toggle
        self.__algorithm_list.itemChanged.connect(self.__update_selected_algorithms)

    def __update_algorithm_helptext(self, item) -> None:
        algorithm = item.data(Qt.ItemDataRole.UserRole)
        self.__algorithm_helptext.set_algorithm(algorithm)

    def __update_selected_algorithms(self, item):
        algorithm = item.data(Qt.ItemDataRole.UserRole)
        if item.checkState() == Qt.CheckState.Checked:
            self.wizard().selected_algorithms.append(algorithm)
        else:
            self.wizard().selected_algorithms.remove(algorithm)
        self.completeChanged.emit()

    def isComplete(self) -> bool:
        # enables the Next button
        # call whenever any item's checkbox changes
        return bool(self.wizard().selected_algorithms)


class AlgorithmResultWidget(QWidget):
    def __init__(self, algorithm: Optional[QgsProcessingAlgorithm] = None, parent: Optional[QObject] = None) -> None:
        super().__init__(parent=parent)
        self.setObjectName(algorithm.id())  # for updating the widgets after running their task

        self.__name_label = QLabel(algorithm.displayName(), self)
        self.__details = QLabel(self)
        self.__verdict = QLabel("?", self)

        self.setMinimumWidth(200)
        self.setMaximumWidth(200)

        layout = QHBoxLayout(self)
        layout.addWidget(self.__name_label)
        layout.addWidget(self.__details)
        layout.addWidget(self.__verdict)
        layout.addStretch(True)

    def set_result(self, result: CheckerResult) -> None:
        self.__verdict.setText("❌" if result.verdict is True else "👍")  # yes, this is reversed! checks are negative
        self.__details.setText(str(result.details))  # TODO make it look nice
        if result.verdict is True:  # noqa
            self.setStyleSheet("background-color:red;")
        else:
            self.setStyleSheet("background-color:green;")


class ChecksResultsPage(QWizardPage):
    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent=parent)

        self.setTitle("Results")
        self.setSubTitle("Results of checks on the current QGIS project")

        execute_button = QPushButton("Execute Checks")
        execute_button.clicked.connect(self.__execute_checks)

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(execute_button)

    def initializePage(self):
        logging.debug("initializePage")

        # TODO put these in a scrollable pane, clear it every time in this function
        for algorithm in self.wizard().selected_algorithms:
            widget = AlgorithmResultWidget(algorithm, self)
            self.layout.addWidget(widget)

    def __execute_checks(self):
        logging.debug("__execute_checks")
        logging.debug(self.wizard().selected_algorithms)
        logging.debug(f"{self.wizard().selected_project=}")
        tasks: list[Task] = []
        algorithm: QgsProcessingAlgorithm
        for algorithm in self.wizard().selected_algorithms:
            task = Task(algorithm.id(), parameters={"PROJECT": self.wizard().selected_project})  # OUTPUT params needed?
            task.runFinished.connect(self.onTaskRunFinished)
            tasks.append(task)
            widget: AlgorithmResultWidget = self.findChild(AlgorithmResultWidget, algorithm.id())
            widget.setStyleSheet("background-color:orange;")

        with wait_cursor():
            for task in tasks:
                task.run()

    def onTaskRunFinished(self, result: CheckerResult):
        logging.debug(f"{result!s}")
        widget: AlgorithmResultWidget = self.findChild(AlgorithmResultWidget, result.algorithm_id)
        widget.set_result(result)
