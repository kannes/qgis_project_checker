import logging

from typing import Optional

from qgis.PyQt.QtCore import QObject, Qt
from qgis.PyQt.QtGui import QFont
from qgis.PyQt.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
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
        self.__select_all_button = QPushButton("Select All")
        self.__select_none_button = QPushButton("Select None")

        buttons_widget = QWidget(self)
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.addWidget(self.__select_all_button)
        buttons_layout.addWidget(self.__select_none_button)
        buttons_layout.addStretch()

        layout = QGridLayout(self)
        layout.addWidget(self.__algorithm_list, 0, 0)
        layout.addWidget(self.__algorithm_helptext, 0, 1)
        layout.addWidget(buttons_widget, 1, 0, 1, 2)

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

        self.__select_all_button.clicked.connect(self.__select_all)
        self.__select_none_button.clicked.connect(self.__select_none)

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

    def __select_all(self):
        for row in range(self.__algorithm_list.count()):
            item = self.__algorithm_list.item(row)
            item.setCheckState(Qt.CheckState.Checked)

    def __select_none(self):
        for row in range(self.__algorithm_list.count()):
            item = self.__algorithm_list.item(row)
            item.setCheckState(Qt.CheckState.Unchecked)

    def isComplete(self) -> bool:
        # enables the Next button
        # call whenever any item's checkbox changes
        return bool(self.wizard().selected_algorithms)


class AlgorithmResultWidget(QFrame):
    def __init__(self, algorithm: Optional[QgsProcessingAlgorithm] = None, parent: Optional[QObject] = None) -> None:
        super().__init__(parent=parent)
        self.setObjectName(algorithm.id())  # for updating the widgets after running their task

        self.setFrameShape(QFrame.Shape.WinPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)

        font = QFont()  # copy of the current font
        font.setBold(True)

        self.__name_label = QLabel(f"{algorithm.displayName()}", self)
        self.__name_label.setFont(font)
        self.__details = QLabel(self)
        self.__verdict = QLabel("?", self)
        self.__verdict.setFont(font)

        layout = QHBoxLayout(self)
        layout.addWidget(self.__name_label)
        layout.addWidget(self.__details)
        layout.addStretch()
        layout.addWidget(self.__verdict)

    def set_result(self, result: CheckerResult) -> None:
        self.__verdict.setText("❌" if result.verdict is True else "👍")  # yes, this is reversed! checks are negative
        if result.details:
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

        self.__results_container = QWidget(self)  # parent?
        results_container_layout = QVBoxLayout()
        self.__results_container.setLayout(results_container_layout)
        # self.__results_container.setLayout(QVBoxLayout())
        self.__results_scrollarea = QScrollArea(self)  # parent?
        self.__results_scrollarea.setWidget(self.__results_container)
        self.__results_scrollarea.setWidgetResizable(True)
        self.__results_scrollarea.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)

        layout = QVBoxLayout(self)
        layout.addWidget(execute_button)  # TODO move to navigation?
        layout.addWidget(self.__results_scrollarea)
        # layout.addWidget(self.__results_container)

    def initializePage(self):
        logging.debug("initializePage")

        for widget in self.__results_container.findChildren(AlgorithmResultWidget):
            widget.deleteLater()

        for algorithm in self.wizard().selected_algorithms:
            widget = AlgorithmResultWidget(algorithm, self)
            self.__results_container.layout().addWidget(widget)

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
