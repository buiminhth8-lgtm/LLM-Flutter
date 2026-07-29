"""Download exceptions with stable API error codes."""

from llm_studio.jobs.exceptions import JobCancelledError


class DownloadError(RuntimeError):
    error_code = "DOWNLOAD_FAILED"


class DownloadCancelledError(JobCancelledError, DownloadError):
    error_code = "DOWNLOAD_CANCELLED"


class DownloadValidationError(DownloadError):
    error_code = "DOWNLOAD_VALIDATION_FAILED"


class DiskSpaceError(DownloadError):
    error_code = "DOWNLOAD_DISK_FULL"


class UnauthorizedRepositoryError(DownloadError):
    error_code = "DOWNLOAD_AUTH_REQUIRED"


class RepositoryNotFoundError(DownloadError):
    error_code = "DOWNLOAD_REPO_NOT_FOUND"


class RevisionNotFoundError(DownloadError):
    error_code = "DOWNLOAD_REVISION_NOT_FOUND"


class DownloadNetworkError(DownloadError):
    error_code = "DOWNLOAD_NETWORK_ERROR"


class DownloadRetryNotAllowedError(DownloadError):
    error_code = "DOWNLOAD_RETRY_NOT_ALLOWED"


class DownloadCancelNotAllowedError(DownloadError):
    error_code = "DOWNLOAD_CANCEL_NOT_ALLOWED"


class DownloadLocalFilesNotFoundError(DownloadError):
    error_code = "DOWNLOAD_LOCAL_FILES_NOT_FOUND"


class DownloadAlreadyRunningError(DownloadError):
    error_code = "DOWNLOAD_ALREADY_RUNNING"


class DownloadModelScanError(DownloadValidationError):
    error_code = "DOWNLOAD_MODEL_SCAN_FAILED"


class DownloadModelUnsupportedError(DownloadValidationError):
    error_code = "DOWNLOAD_MODEL_UNSUPPORTED"
