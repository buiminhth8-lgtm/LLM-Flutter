class TrainingDatasetDto {
  const TrainingDatasetDto({
    required this.datasetId,
    required this.name,
    required this.type,
    required this.status,
    required this.sampleCount,
    required this.approvedSampleCount,
    required this.rejectedSampleCount,
    required this.createdAt,
    required this.updatedAt,
    this.description,
    this.projectId,
    this.metadata = const {},
    this.createdBy,
  });

  factory TrainingDatasetDto.fromMap(
    Map<dynamic, dynamic> map,
  ) => TrainingDatasetDto(
    datasetId: '${map['dataset_id'] ?? map['id'] ?? ''}',
    name: '${map['name'] ?? ''}',
    type: '${map['type'] ?? 'sft'}',
    description: _string(map['description']),
    projectId: _string(map['project_id']),
    status: '${map['status'] ?? 'draft'}',
    sampleCount: (map['sample_count'] as num?)?.toInt() ?? 0,
    approvedSampleCount: (map['approved_sample_count'] as num?)?.toInt() ?? 0,
    rejectedSampleCount: (map['rejected_sample_count'] as num?)?.toInt() ?? 0,
    metadata: _map(map['metadata']),
    createdBy: _string(map['created_by']),
    createdAt: '${map['created_at'] ?? ''}',
    updatedAt: '${map['updated_at'] ?? ''}',
  );

  final String datasetId;
  final String name;
  final String type;
  final String? description;
  final String? projectId;
  final String status;
  final int sampleCount;
  final int approvedSampleCount;
  final int rejectedSampleCount;
  final Map<String, dynamic> metadata;
  final String? createdBy;
  final String createdAt;
  final String updatedAt;
}

class CreateDatasetRequest {
  const CreateDatasetRequest({
    required this.name,
    this.type = 'sft',
    this.description,
    this.projectId,
    this.metadata = const {},
  });

  final String name;
  final String type;
  final String? description;
  final String? projectId;
  final Map<String, dynamic> metadata;

  Map<String, Object?> toMap() => {
    'name': name,
    'type': type,
    if (description != null) 'description': description,
    if (projectId != null) 'project_id': projectId,
    'metadata': metadata,
  };
}

class UpdateDatasetRequest {
  const UpdateDatasetRequest({
    this.name,
    this.type,
    this.description,
    this.projectId,
    this.status,
    this.metadata,
  });

  final String? name;
  final String? type;
  final String? description;
  final String? projectId;
  final String? status;
  final Map<String, dynamic>? metadata;

  Map<String, Object?> toMap() => {
    if (name != null) 'name': name,
    if (type != null) 'type': type,
    if (description != null) 'description': description,
    if (projectId != null) 'project_id': projectId,
    if (status != null) 'status': status,
    if (metadata != null) 'metadata': metadata,
  };
}

String? _string(Object? value) => value == null ? null : '$value';

Map<String, dynamic> _map(Object? value) {
  if (value is! Map) {
    return const {};
  }
  return value.map((key, value) => MapEntry('$key', value));
}
