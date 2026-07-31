class DatasetExportDto {
  const DatasetExportDto({
    required this.exportId,
    required this.datasetId,
    required this.format,
    required this.exportPath,
    required this.sampleCount,
    required this.approvedOnly,
    required this.status,
    required this.createdAt,
    this.exportHash,
  });

  factory DatasetExportDto.fromMap(Map<dynamic, dynamic> map) =>
      DatasetExportDto(
        exportId: '${map['export_id'] ?? map['id'] ?? ''}',
        datasetId: '${map['dataset_id'] ?? ''}',
        format: '${map['format'] ?? map['export_format'] ?? 'sft_jsonl'}',
        exportPath: '${map['export_path'] ?? ''}',
        sampleCount: (map['sample_count'] as num?)?.toInt() ?? 0,
        approvedOnly: map['approved_only'] == true || map['approved_only'] == 1,
        exportHash: map['export_hash'] == null ? null : '${map['export_hash']}',
        status: '${map['status'] ?? 'created'}',
        createdAt: '${map['created_at'] ?? ''}',
      );

  final String exportId;
  final String datasetId;
  final String format;
  final String exportPath;
  final int sampleCount;
  final bool approvedOnly;
  final String? exportHash;
  final String status;
  final String createdAt;
}
