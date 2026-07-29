"""Background job exceptions."""


class JobError(RuntimeError):
    pass


class JobNotFoundError(JobError):
    pass


class JobCancelledError(JobError):
    pass


class JobCancelNotAllowedError(JobError):
    error_code = "JOB_CANCEL_NOT_ALLOWED"


class JobQueueClosedError(JobError):
    pass


class JobNotImplementedError(JobError):
    pass
