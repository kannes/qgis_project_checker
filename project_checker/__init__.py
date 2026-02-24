from project_checker.project_checker_plugin import ProjectCheckerPlugin


def classFactory(iface):
    _ = iface  # use qgis.utils.iface if you need it
    return ProjectCheckerPlugin()
