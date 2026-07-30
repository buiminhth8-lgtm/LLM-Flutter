class NovelPlotThreadDto {
  const NovelPlotThreadDto({
    required this.id,
    required this.projectId,
    required this.title,
    required this.status,
  });

  factory NovelPlotThreadDto.fromMap(Map<dynamic, dynamic> map) =>
      NovelPlotThreadDto(
        id: '${map['id'] ?? ''}',
        projectId: '${map['project_id'] ?? ''}',
        title: '${map['title'] ?? ''}',
        status: '${map['status'] ?? 'open'}',
      );

  final String id;
  final String projectId;
  final String title;
  final String status;
}
