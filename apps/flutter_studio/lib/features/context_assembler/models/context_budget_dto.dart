class ContextBudgetDto {
  const ContextBudgetDto({
    this.maxTokens = 4096,
    this.reservedOutputTokens = 1200,
    this.maxContextTokens = 2500,
    this.maxChars = 12000,
    this.hardLimit = true,
    this.estimatedTokens,
    this.estimatedChars,
  });

  factory ContextBudgetDto.fromMap(Map<dynamic, dynamic> map) =>
      ContextBudgetDto(
        maxTokens: _asInt(map['max_tokens'], 4096),
        reservedOutputTokens: _asInt(map['reserved_output_tokens'], 1200),
        maxContextTokens: _asInt(map['max_context_tokens'], 2500),
        maxChars: _asInt(map['max_chars'], 12000),
        hardLimit: map['hard_limit'] != false,
        estimatedTokens: _asNullableInt(map['estimated_tokens']),
        estimatedChars: _asNullableInt(map['estimated_chars']),
      );

  final int maxTokens;
  final int reservedOutputTokens;
  final int maxContextTokens;
  final int maxChars;
  final bool hardLimit;
  final int? estimatedTokens;
  final int? estimatedChars;

  Map<String, Object?> toMap() => {
    'max_tokens': maxTokens,
    'reserved_output_tokens': reservedOutputTokens,
    'max_context_tokens': maxContextTokens,
    'max_chars': maxChars,
    'hard_limit': hardLimit,
  };

  static int _asInt(Object? value, int fallback) =>
      value is num ? value.toInt() : fallback;

  static int? _asNullableInt(Object? value) =>
      value is num ? value.toInt() : null;
}
