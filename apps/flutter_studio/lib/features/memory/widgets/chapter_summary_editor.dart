import 'package:flutter/material.dart';

import '../models/chapter_summary_version_dto.dart';

class ChapterSummaryEditor extends StatelessWidget {
  const ChapterSummaryEditor({
    super.key,
    required this.chapterController,
    required this.summaryController,
    required this.modelController,
    required this.summaries,
    required this.onLoad,
    required this.onCreate,
    required this.onGenerate,
    required this.onActivate,
  });

  final TextEditingController chapterController;
  final TextEditingController summaryController;
  final TextEditingController modelController;
  final List<ChapterSummaryVersionDto> summaries;
  final VoidCallback onLoad;
  final VoidCallback onCreate;
  final VoidCallback onGenerate;
  final void Function(String summaryId) onActivate;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      TextField(
        key: const Key('memory-summary-chapter-id'),
        controller: chapterController,
        decoration: const InputDecoration(
          labelText: 'Chapter ID',
          border: OutlineInputBorder(),
        ),
        onSubmitted: (_) => onLoad(),
      ),
      const SizedBox(height: 8),
      TextField(
        key: const Key('memory-summary-text'),
        controller: summaryController,
        minLines: 3,
        maxLines: 6,
        decoration: const InputDecoration(
          labelText: 'Manual Summary',
          border: OutlineInputBorder(),
        ),
      ),
      const SizedBox(height: 8),
      Row(
        children: [
          Expanded(
            child: OutlinedButton.icon(
              key: const Key('memory-create-summary'),
              onPressed: onCreate,
              icon: const Icon(Icons.add),
              label: const Text('Create Summary'),
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: TextField(
              key: const Key('memory-summary-model-id'),
              controller: modelController,
              decoration: const InputDecoration(
                labelText: 'Model ID',
                border: OutlineInputBorder(),
              ),
            ),
          ),
        ],
      ),
      const SizedBox(height: 8),
      OutlinedButton.icon(
        key: const Key('memory-generate-summary'),
        onPressed: onGenerate,
        icon: const Icon(Icons.auto_awesome),
        label: const Text('Generate Summary'),
      ),
      const Divider(),
      Expanded(
        child: ListView(
          children: [
            if (summaries.isEmpty)
              const ListTile(title: Text('没有章节摘要版本。'))
            else
              for (final summary in summaries)
                ListTile(
                  title: Text('${summary.summaryType} · ${summary.status}'),
                  subtitle: Text(summary.summaryText),
                  trailing: TextButton(
                    onPressed: () => onActivate(summary.summaryId),
                    child: const Text('Activate'),
                  ),
                ),
          ],
        ),
      ),
    ],
  );
}
