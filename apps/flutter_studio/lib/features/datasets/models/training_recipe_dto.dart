class TrainingRecipeDto {
  const TrainingRecipeDto({
    required this.recipeId,
    required this.datasetVersionId,
    required this.method,
    required this.recommendedConfig,
    required this.userConfig,
    required this.status,
    required this.createdAt,
    required this.updatedAt,
    this.baseModelId,
    this.recommendationReason,
    this.estimatedVramGb,
    this.estimatedTrainTimeMinutes,
    this.warnings = const [],
  });

  factory TrainingRecipeDto.fromMap(Map<dynamic, dynamic> map) =>
      TrainingRecipeDto(
        recipeId: '${map['recipe_id'] ?? map['id'] ?? ''}',
        datasetVersionId: '${map['dataset_version_id'] ?? ''}',
        baseModelId: _string(map['base_model_id']),
        method: '${map['method'] ?? 'qlora'}',
        recommendedConfig: _map(map['recommended_config']),
        userConfig: _map(map['user_config']),
        recommendationReason: _string(map['recommendation_reason']),
        estimatedVramGb: (map['estimated_vram_gb'] as num?)?.toDouble(),
        estimatedTrainTimeMinutes: (map['estimated_train_time_minutes'] as num?)
            ?.toInt(),
        warnings: _mapList(map['warnings']),
        status: '${map['status'] ?? 'draft'}',
        createdAt: '${map['created_at'] ?? ''}',
        updatedAt: '${map['updated_at'] ?? ''}',
      );

  final String recipeId;
  final String datasetVersionId;
  final String? baseModelId;
  final String method;
  final Map<String, dynamic> recommendedConfig;
  final Map<String, dynamic> userConfig;
  final String? recommendationReason;
  final double? estimatedVramGb;
  final int? estimatedTrainTimeMinutes;
  final List<Map<String, dynamic>> warnings;
  final String status;
  final String createdAt;
  final String updatedAt;
}

String? _string(Object? value) => value == null ? null : '$value';

Map<String, dynamic> _map(Object? value) {
  if (value is! Map) {
    return const {};
  }
  return value.map((key, value) => MapEntry('$key', value));
}

List<Map<String, dynamic>> _mapList(Object? value) {
  if (value is! List) {
    return const [];
  }
  return value
      .whereType<Map>()
      .map((item) => item.map((key, value) => MapEntry('$key', value)))
      .toList(growable: false);
}
