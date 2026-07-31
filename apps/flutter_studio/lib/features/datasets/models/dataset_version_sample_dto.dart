class DatasetVersionSampleDto {
  const DatasetVersionSampleDto({
    required this.datasetVersionSampleId,
    required this.datasetVersionId,
    required this.sampleId,
    required this.split,
    required this.sampleOrder,
    required this.contentHash,
    required this.charCount,
    required this.tokenEstimate,
    required this.createdAt,
    this.sourceHash,
    this.duplicateGroupId,
    this.warnings = const [],
  });

  factory DatasetVersionSampleDto.fromMap(Map<dynamic, dynamic> map) =>
      DatasetVersionSampleDto(
        datasetVersionSampleId:
            '${map['dataset_version_sample_id'] ?? map['id'] ?? ''}',
        datasetVersionId: '${map['dataset_version_id'] ?? ''}',
        sampleId: '${map['sample_id'] ?? ''}',
        split: '${map['split'] ?? 'train'}',
        sampleOrder: (map['sample_order'] as num?)?.toInt() ?? 0,
        contentHash: '${map['content_hash'] ?? ''}',
        sourceHash: _string(map['source_hash']),
        charCount: (map['char_count'] as num?)?.toInt() ?? 0,
        tokenEstimate: (map['token_estimate'] as num?)?.toInt() ?? 0,
        duplicateGroupId: _string(map['duplicate_group_id']),
        warnings: _mapList(map['warnings']),
        createdAt: '${map['created_at'] ?? ''}',
      );

  final String datasetVersionSampleId;
  final String datasetVersionId;
  final String sampleId;
  final String split;
  final int sampleOrder;
  final String contentHash;
  final String? sourceHash;
  final int charCount;
  final int tokenEstimate;
  final String? duplicateGroupId;
  final List<Map<String, dynamic>> warnings;
  final String createdAt;
}

String? _string(Object? value) => value == null ? null : '$value';

List<Map<String, dynamic>> _mapList(Object? value) {
  if (value is! List) {
    return const [];
  }
  return value
      .whereType<Map>()
      .map((item) => item.map((key, value) => MapEntry('$key', value)))
      .toList(growable: false);
}
