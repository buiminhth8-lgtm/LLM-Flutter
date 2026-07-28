"""Download exceptions."""


class DownloadError(RuntimeError):
    pass


class DownloadCancelledError(DownloadError):
    pass


class DownloadValidationError(DownloadError):
    pass


class DiskSpaceError(DownloadError):
    pass


class UnauthorizedRepositoryError(DownloadError):
    pass
