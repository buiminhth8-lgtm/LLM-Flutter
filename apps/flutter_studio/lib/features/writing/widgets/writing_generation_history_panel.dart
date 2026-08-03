import 'package:flutter/material.dart';

import '../models/writing_generation_record_dto.dart';

class WritingGenerationHistoryPanel extends StatelessWidget {
  const WritingGenerationHistoryPanel({
    super.key,
    required this.records,
    required this.onSelected,
    this.revisionIdsByGeneration = const {},
    this.onCreateRevision,
    this.onViewRevision,
    this.onEvaluateGeneration,
  });

  final List<WritingGenerationRecordDto> records;
  final ValueChanged<String> onSelected;
  final Map<String, String> revisionIdsByGeneration;
  final ValueChanged<String>? onCreateRevision;
  final ValueChanged<String>? onViewRevision;
  final ValueChanged<String>? onEvaluateGeneration;

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
          _HistoryTile(
            record: record,
            revisionId: revisionIdsByGeneration[record.generationId],
            onSelected: onSelected,
            onCreateRevision: onCreateRevision,
            onViewRevision: onViewRevision,
            onEvaluateGeneration: onEvaluateGeneration,
          ),
    ],
  );
}

class _HistoryTile extends StatelessWidget {
  const _HistoryTile({
    required this.record,
    required this.revisionId,
    required this.onSelected,
    required this.onCreateRevision,
    required this.onViewRevision,
    required this.onEvaluateGeneration,
  });

  final WritingGenerationRecordDto record;
  final String? revisionId;
  final ValueChanged<String> onSelected;
  final ValueChanged<String>? onCreateRevision;
  final ValueChanged<String>? onViewRevision;
  final ValueChanged<String>? onEvaluateGeneration;

  @override
  Widget build(BuildContext context) => ListTile(
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
    trailing: record.status == 'succeeded'
        ? Wrap(
            spacing: 6,
            children: [
              TextButton(
                key: Key('writing-revision-${record.generationId}'),
                onPressed: revisionId == null
                    ? () => onCreateRevision?.call(record.generationId)
                    : () => onViewRevision?.call(revisionId!),
                child: Text(
                  revisionId == null ? 'Create Revision' : 'View Revision',
                ),
              ),
              TextButton(
                key: Key('writing-evaluate-${record.generationId}'),
                onPressed: onEvaluateGeneration == null
                    ? null
                    : () => onEvaluateGeneration?.call(record.generationId),
                child: const Text('Evaluate'),
              ),
            ],
          )
        : null,
    onTap: () => onSelected(record.generationId),
  );
}
