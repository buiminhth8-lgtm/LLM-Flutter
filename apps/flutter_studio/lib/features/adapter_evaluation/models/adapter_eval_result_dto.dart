class AdapterEvalResultDto {
  const AdapterEvalResultDto({
    required this.resultId,
    required this.caseId,
    required this.sessionId,
    required this.variant,
    required this.modelId,
    required this.status,
    required this.outputText,
    this.adapterId,
    this.finishReason,
    this.outputCharCount = 0,
    this.outputTokenEstimate = 0,
    this.latencyMs,
    this.errorCode,
    this.errorMessage,
  });

  final String resultId;
  final String caseId;
  final String sessionId;
  final String variant;
  final String modelId;
  final String? adapterId;
  final String status;
  final String outputText;
  final String? finishReason;
  final int outputCharCount;
  final int outputTokenEstimate;
  final int? latencyMs;
  final String? errorCode;
  final String? errorMessage;

  factory AdapterEvalResultDto.fromMap(Object? value) {
    final map = Map<String, dynamic>.from((value as Map?) ?? const {});
    return AdapterEvalResultDto(
      resultId: '${map['result_id'] ?? ''}',
      caseId: '${map['case_id'] ?? ''}',
      sessionId: '${map['session_id'] ?? ''}',
      variant: '${map['variant'] ?? ''}',
      modelId: '${map['model_id'] ?? ''}',
      adapterId: map['adapter_id']?.toString(),
      status: '${map['status'] ?? ''}',
      outputText: '${map['output_text'] ?? ''}',
      finishReason: map['finish_reason']?.toString(),
      outputCharCount: (map['output_char_count'] as num?)?.toInt() ?? 0,
      outputTokenEstimate: (map['output_token_estimate'] as num?)?.toInt() ?? 0,
      latencyMs: (map['latency_ms'] as num?)?.toInt(),
      errorCode: map['error_code']?.toString(),
      errorMessage: map['error_message']?.toString(),
    );
  }
}
