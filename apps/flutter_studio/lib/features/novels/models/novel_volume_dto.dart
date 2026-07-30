class NovelVolumeDto {
  const NovelVolumeDto({
    required this.id,
    required this.projectId,
    required this.title,
    required this.volumeIndex,
    required this.status,
    this.outline,
  });

  factory NovelVolumeDto.fromMap(Map<dynamic, dynamic> map) => NovelVolumeDto(
    id: '${map['id'] ?? ''}',
    projectId: '${map['project_id'] ?? ''}',
    title: '${map['title'] ?? ''}',
    volumeIndex: map['volume_index'] is num
        ? (map['volume_index'] as num).toInt()
        : 0,
    outline: map['outline'] == null ? null : '${map['outline']}',
    status: '${map['status'] ?? 'active'}',
  );

  final String id;
  final String projectId;
  final String title;
  final int volumeIndex;
  final String? outline;
  final String status;
}
