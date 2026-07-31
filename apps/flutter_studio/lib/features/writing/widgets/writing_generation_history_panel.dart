import 'package:flutter/material.dart';

import '../models/writing_generation_record_dto.dart';

class WritingGenerationHistoryPanel extends StatelessWidget {
  const WritingGenerationHistoryPanel({
    super.key,
    required this.records,
    required this.onSelected,
  });

  final List<WritingGenerationRecordDto> records;
  final ValueChanged<String> onSelected;

  @override
  Widget build(BuildContext context) => ExpansionTile(
    key: const Key('writing-generation-history'),
    initiallyExpanded: true,
    title: Text('生成历史 (${records.length})'),
    children: [
      if (records.isEmpty)
        const ListTile(title: Text('当前章节还没有生成记录。'))
      else
        for (final record in records)
          ListTile(
            dense: true,
            leading: Icon(
              record.status == 'succeeded'
                  ? Icons.check_circle_outline
                  : record.status == 'failed'
                  ? Icons.error_outline
                  : Icons.pending_outlined,
            ),
            title: Text('${record.mode} · ${record.status}'),
            subtitle: Text(
              '${record.outputCharCount} chars · ${record.createdAt}',
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
            onTap: () => onSelected(record.generationId),
          ),
    ],
  );
}
