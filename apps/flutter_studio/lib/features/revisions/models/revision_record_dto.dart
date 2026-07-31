import 'revision_diff_dto.dart';

class RevisionRecordDto {
  const RevisionRecordDto({
    required this.revisionId,
    required this.projectId,
    required this.originalText,
    required this.editedText,
    required this.diff,
    required this.editTags,
    required this.status,
    required this.acceptedForDataset,
    required this.source,
    required this.originalHash,
    required this.editedHash,
    required this.createdAt,
    required this.updatedAt,
    this.generationId,
    this.chapterId,
    this.sceneId,
    this.userScore,
    this.qualityNotes,
    this.reviewerId,
    this.warnings = const [],
  });

  factory RevisionRecordDto.fromMap(Map<dynamic, dynamic> map) {
    final rawDiff = map['diff_json'] ?? map['diff'];
    return RevisionRecordDto(
      revisionId: '${map['revision_id'] ?? map['id'] ?? ''}',
      generationId: _string(map['generation_id']),
      projectId: '${map['project_id'] ?? ''}',
      chapterId: _string(map['chapter_id']),
      sceneId: _string(map['scene_id']),
      originalText: '${map['original_text'] ?? ''}',
      editedText: '${map['edited_text'] ?? ''}',
      diff: RevisionDiffDto.fromMap(rawDiff is Map ? rawDiff : const {}),
      editTags: _stringList(map['edit_tags']),
      userScore: (map['user_score'] as num?)?.toInt(),
      qualityNotes: _string(map['quality_notes']),
      status: '${map['status'] ?? 'draft'}',
      acceptedForDataset:
          map['accepted_for_dataset'] == true ||
          map['accepted_for_dataset'] == 1,
      reviewerId: _string(map['reviewer_id']),
      source: '${map['source'] ?? 'manual'}',
      originalHash: '${map['original_hash'] ?? ''}',
      editedHash: '${map['edited_hash'] ?? ''}',
      createdAt: '${map['created_at'] ?? ''}',
      updatedAt: '${map['updated_at'] ?? ''}',
      warnings: _mapList(map['warnings']),
    );
  }

  final String revisionId;
  final String? generationId;
  final String projectId;
  final String? chapterId;
  final String? sceneId;
  final String originalText;
  final String editedText;
  final RevisionDiffDto diff;
  final List<String> editTags;
  final int? userScore;
  final String? qualityNotes;
  final String status;
  final bool acceptedForDataset;
  final String? reviewerId;
  final String source;
  final String originalHash;
  final String editedHash;
  final String createdAt;
  final String updatedAt;
  final List<Map<String, dynamic>> warnings;
}

class RevisionUpdateRequest {
  const RevisionUpdateRequest({
    this.editedText,
    this.editTags,
    this.userScore,
    this.qualityNotes,
    this.status,
    this.acceptedForDataset,
    this.reviewerId,
    this.expectedUpdatedAt,
  });

  final String? editedText;
  final List<String>? editTags;
  final int? userScore;
  final String? qualityNotes;
  final String? status;
  final bool? acceptedForDataset;
  final String? reviewerId;
  final String? expectedUpdatedAt;

  Map<String, Object?> toMap() => {
    if (editedText != null) 'edited_text': editedText,
    if (editTags != null) 'edit_tags': editTags,
    if (userScore != null) 'user_score': userScore,
    if (qualityNotes != null) 'quality_notes': qualityNotes,
    if (status != null) 'status': status,
    if (acceptedForDataset != null) 'accepted_for_dataset': acceptedForDataset,
    if (reviewerId != null) 'reviewer_id': reviewerId,
    if (expectedUpdatedAt != null) 'expected_updated_at': expectedUpdatedAt,
  };
}

String? _string(Object? value) => value == null ? null : '$value';

List<String> _stringList(Object? value) {
  if (value is! List) {
    return const [];
  }
  return value.map((item) => '$item').toList(growable: false);
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
