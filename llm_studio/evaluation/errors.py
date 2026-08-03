"""Stable Evaluation Center errors."""

from __future__ import annotations

from llm_studio.api import errors as api_errors


class EvaluationError(ValueError):
    code = api_errors.EVALUATION_RUN_FAILED
    status_code = 400

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class EvaluationFeatureDisabledError(EvaluationError):
    code = api_errors.EVALUATION_FEATURE_DISABLED
    status_code = 404


class EvaluationRunNotFoundError(EvaluationError):
    code = api_errors.EVALUATION_RUN_NOT_FOUND
    status_code = 404

    def __init__(self, run_id: str):
        super().__init__(f"Evaluation run not found: {run_id}")


class EvaluationCaseNotFoundError(EvaluationError):
    code = api_errors.EVALUATION_CASE_NOT_FOUND
    status_code = 404

    def __init__(self, case_id: str):
        super().__init__(f"Evaluation case not found: {case_id}")


class EvaluationReportNotFoundError(EvaluationError):
    code = api_errors.EVALUATION_REPORT_NOT_FOUND
    status_code = 404

    def __init__(self, report_id: str):
        super().__init__(f"Evaluation report not found: {report_id}")


class EvaluationFindingNotFoundError(EvaluationError):
    code = api_errors.EVALUATION_FINDING_NOT_FOUND
    status_code = 404

    def __init__(self, finding_id: str):
        super().__init__(f"Evaluation finding not found: {finding_id}")


class EvaluationTargetNotFoundError(EvaluationError):
    code = api_errors.EVALUATION_TARGET_NOT_FOUND
    status_code = 404


class EvaluationInvalidTargetTypeError(EvaluationError):
    code = api_errors.EVALUATION_INVALID_TARGET_TYPE


class EvaluationInvalidEvaluatorError(EvaluationError):
    code = api_errors.EVALUATION_INVALID_EVALUATOR


class EvaluationTextEmptyError(EvaluationError):
    code = api_errors.EVALUATION_TEXT_EMPTY


class EvaluationRunFailedError(EvaluationError):
    code = api_errors.EVALUATION_RUN_FAILED
    status_code = 500


class EvaluationCancelNotSupportedError(EvaluationError):
    code = api_errors.EVALUATION_CANCEL_NOT_SUPPORTED
    status_code = 409


class EvaluationMetricFailedError(EvaluationError):
    code = api_errors.EVALUATION_METRIC_FAILED
    status_code = 500


class EvaluationReportFailedError(EvaluationError):
    code = api_errors.EVALUATION_REPORT_FAILED
    status_code = 500


class EvaluationInvalidScoreError(EvaluationError):
    code = api_errors.EVALUATION_INVALID_SCORE


class EvaluationLocalModelNotFoundError(EvaluationError):
    code = api_errors.EVALUATION_LOCAL_MODEL_NOT_FOUND
    status_code = 404


class EvaluationLocalModelNotLoadedError(EvaluationError):
    code = api_errors.EVALUATION_LOCAL_MODEL_NOT_LOADED
    status_code = 409


class EvaluationLocalModelJudgeFailedError(EvaluationError):
    code = api_errors.EVALUATION_LOCAL_MODEL_JUDGE_FAILED
    status_code = 500

