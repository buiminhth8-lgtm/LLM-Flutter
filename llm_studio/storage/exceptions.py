"""Storage exceptions."""


class StorageError(RuntimeError):
    pass


class UnsafeCleanupError(StorageError):
    pass
