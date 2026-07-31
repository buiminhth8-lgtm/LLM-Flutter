class DatasetFilterDto {
  const DatasetFilterDto({
    this.projectId,
    this.type,
    this.status,
    this.minScore,
    this.tags = const [],
  });

  final String? projectId;
  final String? type;
  final String? status;
  final int? minScore;
  final List<String> tags;
}
