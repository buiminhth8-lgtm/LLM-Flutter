"""Adapter exceptions."""


class AdapterError(RuntimeError):
    pass


class AdapterNotFoundError(AdapterError):
    pass


class AdapterCompatibilityError(AdapterError):
    pass
