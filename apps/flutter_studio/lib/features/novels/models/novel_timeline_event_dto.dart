class NovelTimelineEventDto {
  const NovelTimelineEventDto({
    required this.id,
    required this.projectId,
    required this.title,
    required this.eventOrder,
  });

  factory NovelTimelineEventDto.fromMap(Map<dynamic, dynamic> map) =>
      NovelTimelineEventDto(
        id: '${map['id'] ?? ''}',
        projectId: '${map['project_id'] ?? ''}',
        title: '${map['title'] ?? ''}',
        eventOrder: map['event_order'] is num
            ? (map['event_order'] as num).toInt()
            : 0,
      );

  final String id;
  final String projectId;
  final String title;
  final int eventOrder;
}
