"""Model repository exceptions."""


class ModelRepositoryError(RuntimeError):
    pass


class InvalidModelPathError(ModelRepositoryError):
    pass


class ModelDeleteError(ModelRepositoryError):
    pass


class ModelCompatibilityError(ModelRepositoryError):
    pass
