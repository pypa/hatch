class HatchError(Exception):
    pass


class PythonDistributionUnknownError(HatchError):
    pass


class PythonDistributionResolutionError(HatchError):
    pass
