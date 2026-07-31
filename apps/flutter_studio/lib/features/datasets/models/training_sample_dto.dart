class TrainingSampleDto {
  const TrainingSampleDto({
    required this.sampleId,
    required this.datasetId,
    required this.sampleType,
    required this.instruction,
    required this.input,
    required this.output,
    required this.sourceHash,
    required this.contentHash,
    required this.status,
    required this.createdAt,
    required this.updatedAt,
    this.projectId,
    this.chapterId,
    this.revisionId,
    this.generationId,
    this.chosen,
    this.rejected,
    this.qualityScore,
    this.reviewNotes,
    this.metadata = const {},
    this.warnings = const [],
  });

  factory TrainingSampleDto.fromMap(Map<dynamic, dynamic> map) =>
      TrainingSampleDto(
        sampleId: '${map['sample_id'] ?? map['id'] ?? ''}',
        datasetId: '${map['dataset_id'] ?? ''}',
        projectId: _string(map['project_id']),
        chapterId: _string(map['chapter_id']),
        revisionId: _string(map['revision_id']),
        generationId: _string(map['generation_id']),
        sampleType: '${map['sample_type'] ?? 'sft'}',
        instruction: '${map['instruction'] ?? ''}',
        input: '${map['input'] ?? ''}',
        output: '${map['output'] ?? ''}',
        chosen: _string(map['chosen']),
        rejected: _string(map['rejected']),
        metadata: _map(map['metadata']),
        warnings: _mapList(map['warnings']),
        sourceHash: '${map['source_hash'] ?? ''}',
        contentHash: '${map['content_hash'] ?? ''}',
        qualityScore: (map['quality_score'] as num?)?.toInt(),
        status: '${map['status'] ?? 'pending'}',
        reviewNotes: _string(map['review_notes']),
        createdAt: '${map['created_at'] ?? ''}',
        updatedAt: '${map['updated_at'] ?? ''}',
      );

  final String sampleId;
  final String datasetId;
  final String? projectId;
  final String? chapterId;
  final String? revisionId;
  final String? generationId;
  final String sampleType;
  final String instruction;
  final String input;
  final String output;
  final String? chosen;
  final String? rejected;
  final Map<String, dynamic> metadata;
  final List<Map<String, dynamic>> warnings;
  final String sourceHash;
  final String contentHash;
  final int? qualityScore;
  final String status;
  final String? reviewNotes;
  final String createdAt;
  final String updatedAt;
}

class UpdateSampleRequest {
  const UpdateSampleRequest({
    this.instruction,
    this.input,
    this.output,
    this.chosen,
    this.rejected,
    this.qualityScore,
    this.status,
    this.reviewNotes,
    this.metadata,
  });

  final String? instruction;
  final String? input;
  final String? output;
  final String? chosen;
  final String? rejected;
  final int? qualityScore;
  final String? status;
  final String? reviewNotes;
  final Map<String, dynamic>? metadata;

  Map<String, Object?> toMap() => {
    if (instruction != null) 'instruction': instruction,
    if (input != null) 'input': input,
    if (output != null) 'output': output,
    if (chosen != null) 'chosen': chosen,
    if (rejected != null) 'rejected': rejected,
    if (qualityScore != null) 'quality_score': qualityScore,
    if (status != null) 'status': status,
    if (reviewNotes != null) 'review_notes': reviewNotes,
    if (metadata != null) 'metadata': metadata,
  };
}

class BulkCreateSamplesResultDto {
  const BulkCreateSamplesResultDto({
    required this.createdCount,
    required this.errorCount,
    this.samples = const [],
    this.errors = const [],
  });

  factory BulkCreateSamplesResultDto.fromMap(Map<dynamic, dynamic> map) =>
      BulkCreateSamplesResultDto(
        createdCount: (map['created_count'] as num?)?.toInt() ?? 0,
        errorCount: (map['error_count'] as num?)?.toInt() ?? 0,
        samples: ((map['samples'] as List?) ?? const [])
            .whereType<Map>()
            .map(TrainingSampleDto.fromMap)
            .toList(growable: false),
        errors: _mapList(map['errors']),
      );

  final int createdCount;
  final int errorCount;
  final List<TrainingSampleDto> samples;
  final List<Map<String, dynamic>> errors;
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
