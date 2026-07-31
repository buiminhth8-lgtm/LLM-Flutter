class DatasetManifestDto {
  const DatasetManifestDto({
    required this.datasetVersionId,
    required this.datasetId,
    required this.version,
    required this.format,
    this.split = const {},
    this.counts = const {},
    this.stats = const {},
    this.hashes = const {},
    this.warnings = const [],
  });

  factory DatasetManifestDto.fromMap(Map<dynamic, dynamic> map) =>
      DatasetManifestDto(
        datasetVersionId: '${map['dataset_version_id'] ?? ''}',
        datasetId: '${map['dataset_id'] ?? ''}',
        version: (map['version'] as num?)?.toInt() ?? 0,
        format: '${map['format'] ?? 'sft_jsonl'}',
        split: _map(map['split']),
        counts: _map(map['counts']),
        stats: _map(map['stats']),
        hashes: _map(map['hashes']),
        warnings: _mapList(map['warnings']),
      );

  final String datasetVersionId;
  final String datasetId;
  final int version;
  final String format;
  final Map<String, dynamic> split;
  final Map<String, dynamic> counts;
  final Map<String, dynamic> stats;
  final Map<String, dynamic> hashes;
  final List<Map<String, dynamic>> warnings;
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
