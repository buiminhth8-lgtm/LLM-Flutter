class ChapterSummaryVersionDto {
  const ChapterSummaryVersionDto({
    required this.summaryId,
    required this.projectId,
    required this.chapterId,
    this.summaryType = 'short',
    required this.summaryText,
    this.sourceTextHash = '',
    this.generatedBy = 'manual',
    this.modelId,
    this.promptTemplateId,
    this.status = 'active',
    this.createdAt = '',
  });

  final String summaryId;
  final String projectId;
  final String chapterId;
  final String summaryType;
  final String summaryText;
  final String sourceTextHash;
  final String generatedBy;
  final String? modelId;
  final String? promptTemplateId;
  final String status;
  final String createdAt;

  factory ChapterSummaryVersionDto.fromMap(Map<dynamic, dynamic> map) =>
      ChapterSummaryVersionDto(
        summaryId: '${map['summary_id'] ?? map['id'] ?? ''}',
        projectId: '${map['project_id'] ?? ''}',
        chapterId: '${map['chapter_id'] ?? ''}',
        summaryType: '${map['summary_type'] ?? 'short'}',
        summaryText: '${map['summary_text'] ?? ''}',
        sourceTextHash: '${map['source_text_hash'] ?? ''}',
        generatedBy: '${map['generated_by'] ?? 'manual'}',
        modelId: map['model_id'] == null ? null : '${map['model_id']}',
        promptTemplateId: map['prompt_template_id'] == null
            ? null
            : '${map['prompt_template_id']}',
        status: '${map['status'] ?? 'active'}',
        createdAt: '${map['created_at'] ?? ''}',
      );
}
