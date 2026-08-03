class FinetunePreflightRequestDto {
  const FinetunePreflightRequestDto({
    required this.datasetVersionId,
    required this.recipeId,
    required this.baseModelId,
    required this.adapterName,
  });

  final String datasetVersionId;
  final String recipeId;
  final String baseModelId;
  final String adapterName;

  Map<String, Object?> toMap() => {
    'dataset_version_id': datasetVersionId,
    'recipe_id': recipeId,
    'base_model_id': baseModelId,
    'adapter_name': adapterName,
  };
}

class FinetunePreflightDto {
  const FinetunePreflightDto({
    required this.ok,
    this.errors = const [],
    this.warnings = const [],
    this.resolvedConfig = const {},
  });

  factory FinetunePreflightDto.fromMap(Map<dynamic, dynamic> map) =>
      FinetunePreflightDto(
        ok: map['ok'] == true,
        errors: _mapList(map['errors']),
        warnings: _mapList(map['warnings']),
        resolvedConfig: _map(map['resolved_config']),
      );

  final bool ok;
  final List<Map<String, dynamic>> errors;
  final List<Map<String, dynamic>> warnings;
  final Map<String, dynamic> resolvedConfig;
}

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
