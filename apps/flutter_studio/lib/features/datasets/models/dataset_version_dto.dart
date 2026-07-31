class DatasetVersionDto {
  const DatasetVersionDto({
    required this.datasetVersionId,
    required this.datasetId,
    required this.version,
    required this.name,
    required this.status,
    required this.sourceSampleCount,
    required this.trainSampleCount,
    required this.valSampleCount,
    required this.rejectedDuplicateCount,
    required this.warningCount,
    required this.trainCharCount,
    required this.valCharCount,
    required this.trainTokenEstimate,
    required this.valTokenEstimate,
    required this.contentHash,
    required this.manifestPath,
    required this.trainPath,
    required this.createdAt,
    this.description,
    this.valPath,
    this.metadata = const {},
    this.warnings = const [],
  });

  factory DatasetVersionDto.fromMap(Map<dynamic, dynamic> map) =>
      DatasetVersionDto(
        datasetVersionId: '${map['dataset_version_id'] ?? map['id'] ?? ''}',
        datasetId: '${map['dataset_id'] ?? ''}',
        version: (map['version'] as num?)?.toInt() ?? 0,
        name: '${map['name'] ?? ''}',
        description: _string(map['description']),
        status: '${map['status'] ?? 'frozen'}',
        sourceSampleCount: (map['source_sample_count'] as num?)?.toInt() ?? 0,
        trainSampleCount: (map['train_sample_count'] as num?)?.toInt() ?? 0,
        valSampleCount: (map['val_sample_count'] as num?)?.toInt() ?? 0,
        rejectedDuplicateCount:
            (map['rejected_duplicate_count'] as num?)?.toInt() ?? 0,
        warningCount: (map['warning_count'] as num?)?.toInt() ?? 0,
        trainCharCount: (map['train_char_count'] as num?)?.toInt() ?? 0,
        valCharCount: (map['val_char_count'] as num?)?.toInt() ?? 0,
        trainTokenEstimate: (map['train_token_estimate'] as num?)?.toInt() ?? 0,
        valTokenEstimate: (map['val_token_estimate'] as num?)?.toInt() ?? 0,
        contentHash: '${map['content_hash'] ?? ''}',
        manifestPath: '${map['manifest_path'] ?? ''}',
        trainPath: '${map['train_path'] ?? ''}',
        valPath: _string(map['val_path']),
        metadata: _map(map['metadata']),
        warnings: _mapList(map['warnings']),
        createdAt: '${map['created_at'] ?? ''}',
      );

  final String datasetVersionId;
  final String datasetId;
  final int version;
  final String name;
  final String? description;
  final String status;
  final int sourceSampleCount;
  final int trainSampleCount;
  final int valSampleCount;
  final int rejectedDuplicateCount;
  final int warningCount;
  final int trainCharCount;
  final int valCharCount;
  final int trainTokenEstimate;
  final int valTokenEstimate;
  final String contentHash;
  final String manifestPath;
  final String trainPath;
  final String? valPath;
  final Map<String, dynamic> metadata;
  final List<Map<String, dynamic>> warnings;
  final String createdAt;
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
