import 'package:flutter/material.dart';

import '../../novels/models/novel_chapter_dto.dart';

class WritingChapterSelector extends StatelessWidget {
  const WritingChapterSelector({
    super.key,
    required this.chapters,
    required this.value,
    required this.onChanged,
  });

  final List<NovelChapterDto> chapters;
  final String? value;
  final ValueChanged<String?> onChanged;

  @override
  Widget build(BuildContext context) => DropdownButtonFormField<String>(
    key: const Key('writing-chapter-selector'),
    initialValue: value,
    isExpanded: true,
    items: [
      for (final chapter in chapters)
        DropdownMenuItem(
          value: chapter.id,
          child: Text('${chapter.chapterIndex}. ${chapter.title}'),
        ),
    ],
    onChanged: onChanged,
    decoration: const InputDecoration(
      labelText: '章节',
      border: OutlineInputBorder(),
    ),
  );
}
