class RevisionAutosaveDto {
  const RevisionAutosaveDto({
    required this.autosaveId,
    required this.projectId,
    required this.draftText,
    required this.draftHash,
    required this.clientRevision,
    required this.createdAt,
    this.revisionId,
    this.chapterId,
    this.generationId,
    this.baseTextHash,
  });

  factory RevisionAutosaveDto.fromMap(Map<dynamic, dynamic> map) =>
      RevisionAutosaveDto(
        autosaveId: '${map['autosave_id'] ?? map['id'] ?? ''}',
        revisionId: map['revision_id'] == null ? null : '${map['revision_id']}',
        projectId: '${map['project_id'] ?? ''}',
        chapterId: map['chapter_id'] == null ? null : '${map['chapter_id']}',
        generationId: map['generation_id'] == null
            ? null
            : '${map['generation_id']}',
        draftText: '${map['draft_text'] ?? ''}',
        baseTextHash: map['base_text_hash'] == null
            ? null
            : '${map['base_text_hash']}',
        draftHash: '${map['draft_hash'] ?? ''}',
        clientRevision: (map['client_revision'] as num?)?.toInt() ?? 1,
        createdAt: '${map['created_at'] ?? ''}',
      );

  final String autosaveId;
  final String? revisionId;
  final String projectId;
  final String? chapterId;
  final String? generationId;
  final String draftText;
  final String? baseTextHash;
  final String draftHash;
  final int clientRevision;
  final String createdAt;
}

class RevisionAutosaveRequest {
  const RevisionAutosaveRequest({
    required this.projectId,
    required this.draftText,
    this.revisionId,
    this.chapterId,
    this.generationId,
    this.baseTextHash,
    this.clientRevision = 1,
  });

  final String? revisionId;
  final String projectId;
  final String? chapterId;
  final String? generationId;
  final String draftText;
  final String? baseTextHash;
  final int clientRevision;

  Map<String, Object?> toMap() => {
    if (revisionId != null) 'revision_id': revisionId,
    'project_id': projectId,
    if (chapterId != null) 'chapter_id': chapterId,
    if (generationId != null) 'generation_id': generationId,
    'draft_text': draftText,
    if (baseTextHash != null) 'base_text_hash': baseTextHash,
    'client_revision': clientRevision,
  };
}
