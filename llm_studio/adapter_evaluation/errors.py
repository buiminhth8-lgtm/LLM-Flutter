"""Stable errors for Novel Studio Stage 9 Adapter Evaluation."""

from __future__ import annotations


class AdapterEvaluationError(RuntimeError):
    code = "ADAPTER_EVAL_GENERATION_FAILED"
    status_code = 400

    def __init__(self, message: str, *, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class AdapterEvalFeatureDisabledError(AdapterEvaluationError):
    code = "ADAPTER_EVAL_FEATURE_DISABLED"
    status_code = 404


class AdapterEvalSessionNotFoundError(AdapterEvaluationError):
    code = "ADAPTER_EVAL_SESSION_NOT_FOUND"
    status_code = 404


class AdapterEvalCaseNotFoundError(AdapterEvaluationError):
    code = "ADAPTER_EVAL_CASE_NOT_FOUND"
    status_code = 404


class AdapterEvalResultNotFoundError(AdapterEvaluationError):
    code = "ADAPTER_EVAL_RESULT_NOT_FOUND"
    status_code = 404


class AdapterEvalScoreNotFoundError(AdapterEvaluationError):
    code = "ADAPTER_EVAL_SCORE_NOT_FOUND"
    status_code = 404


class AdapterEvalReportNotFoundError(AdapterEvaluationError):
    code = "ADAPTER_EVAL_REPORT_NOT_FOUND"
    status_code = 404


class AdapterEvalBaseModelNotFoundError(AdapterEvaluationError):
    code = "ADAPTER_EVAL_BASE_MODEL_NOT_FOUND"
    status_code = 404


class AdapterEvalAdapterNotFoundError(AdapterEvaluationError):
    code = "ADAPTER_EVAL_ADAPTER_NOT_FOUND"
    status_code = 404


class AdapterEvalAdapterIncompatibleError(AdapterEvaluationError):
    code = "ADAPTER_EVAL_ADAPTER_INCOMPATIBLE"


class AdapterEvalFineTuneRunNotFoundError(AdapterEvaluationError):
    code = "ADAPTER_EVAL_FINETUNE_RUN_NOT_FOUND"
    status_code = 404


class AdapterEvalFineTuneRunNotCompletedError(AdapterEvaluationError):
    code = "ADAPTER_EVAL_FINETUNE_RUN_NOT_COMPLETED"


class AdapterEvalProjectNotFoundError(AdapterEvaluationError):
    code = "ADAPTER_EVAL_PROJECT_NOT_FOUND"
    status_code = 404


class AdapterEvalChapterNotFoundError(AdapterEvaluationError):
    code = "ADAPTER_EVAL_CHAPTER_NOT_FOUND"
    status_code = 404


class AdapterEvalTemplateNotFoundError(AdapterEvaluationError):
    code = "ADAPTER_EVAL_TEMPLATE_NOT_FOUND"
    status_code = 404


class AdapterEvalContextFailedError(AdapterEvaluationError):
    code = "ADAPTER_EVAL_CONTEXT_FAILED"


class AdapterEvalPromptRenderFailedError(AdapterEvaluationError):
    code = "ADAPTER_EVAL_PROMPT_RENDER_FAILED"


class AdapterEvalGenerationFailedError(AdapterEvaluationError):
    code = "ADAPTER_EVAL_GENERATION_FAILED"
    status_code = 500


class AdapterEvalInvalidScoreError(AdapterEvaluationError):
    code = "ADAPTER_EVAL_INVALID_SCORE"


class AdapterEvalInvalidWinnerError(AdapterEvaluationError):
    code = "ADAPTER_EVAL_INVALID_WINNER"


class AdapterEvalCaseNotReadyError(AdapterEvaluationError):
    code = "ADAPTER_EVAL_CASE_NOT_READY"
    status_code = 409


class AdapterEvalResultPairIncompleteError(AdapterEvaluationError):
    code = "ADAPTER_EVAL_RESULT_PAIR_INCOMPLETE"
    status_code = 409


class AdapterEvalReportFailedError(AdapterEvaluationError):
    code = "ADAPTER_EVAL_REPORT_FAILED"
    status_code = 500


class AdapterEvalRevisionCreateFailedError(AdapterEvaluationError):
    code = "ADAPTER_EVAL_REVISION_CREATE_FAILED"
    status_code = 500


class AdapterEvalPermissionDeniedError(AdapterEvaluationError):
    code = "ADAPTER_EVAL_PERMISSION_DENIED"
    status_code = 403
