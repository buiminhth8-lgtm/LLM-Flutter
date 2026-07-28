"""Background job exceptions."""


class JobError(RuntimeError):
    pass


class JobNotFoundError(JobError):
    pass


class JobCancelledError(JobError):
    pass


class JobQueueClosedError(JobError):
    pass


class JobNotImplementedError(JobError):
    pass
