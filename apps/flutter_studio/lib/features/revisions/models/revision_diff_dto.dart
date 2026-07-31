class RevisionDiffDto {
  const RevisionDiffDto({required this.summary, required this.ops});

  factory RevisionDiffDto.fromMap(Map<dynamic, dynamic> map) {
    final rawOps = map['ops'];
    return RevisionDiffDto(
      summary: RevisionDiffSummaryDto.fromMap(
        map['summary'] is Map ? map['summary'] as Map : const {},
      ),
      ops: rawOps is List
          ? rawOps
                .whereType<Map>()
                .map(RevisionDiffOpDto.fromMap)
                .toList(growable: false)
          : const [],
    );
  }

  final RevisionDiffSummaryDto summary;
  final List<RevisionDiffOpDto> ops;
}

class RevisionDiffSummaryDto {
  const RevisionDiffSummaryDto({
    required this.originalChars,
    required this.editedChars,
    required this.addedChars,
    required this.removedChars,
    required this.changedBlocks,
  });

  factory RevisionDiffSummaryDto.fromMap(Map<dynamic, dynamic> map) =>
      RevisionDiffSummaryDto(
        originalChars: (map['original_chars'] as num?)?.toInt() ?? 0,
        editedChars: (map['edited_chars'] as num?)?.toInt() ?? 0,
        addedChars: (map['added_chars'] as num?)?.toInt() ?? 0,
        removedChars: (map['removed_chars'] as num?)?.toInt() ?? 0,
        changedBlocks: (map['changed_blocks'] as num?)?.toInt() ?? 0,
      );

  final int originalChars;
  final int editedChars;
  final int addedChars;
  final int removedChars;
  final int changedBlocks;
}

class RevisionDiffOpDto {
  const RevisionDiffOpDto({required this.type, required this.text});

  factory RevisionDiffOpDto.fromMap(Map<dynamic, dynamic> map) =>
      RevisionDiffOpDto(
        type: '${map['type'] ?? 'equal'}',
        text: '${map['text'] ?? ''}',
      );

  final String type;
  final String text;
}
