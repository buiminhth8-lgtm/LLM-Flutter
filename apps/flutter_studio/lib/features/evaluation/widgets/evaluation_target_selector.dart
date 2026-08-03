import 'package:flutter/material.dart';

import '../evaluation_api_client.dart';

class EvaluationTargetSelector extends StatelessWidget {
  const EvaluationTargetSelector({
    super.key,
    required this.targetType,
    required this.targetIdController,
    required this.projectIdController,
    required this.chapterIdController,
    required this.onTargetTypeChanged,
  });

  final String targetType;
  final TextEditingController targetIdController;
  final TextEditingController projectIdController;
  final TextEditingController chapterIdController;
  final ValueChanged<String> onTargetTypeChanged;

  @override
  Widget build(BuildContext context) => Column(
    children: [
      DropdownButtonFormField<String>(
        key: const Key('evaluation-target-type'),
        initialValue: targetType,
        items: [
          for (final entry in evaluationTargetTypeLabels.entries)
            DropdownMenuItem(value: entry.key, child: Text(entry.value)),
        ],
        decoration: const InputDecoration(
          labelText: '目标类型',
          border: OutlineInputBorder(),
        ),
        onChanged: (value) {
          if (value != null) {
            onTargetTypeChanged(value);
          }
        },
      ),
      const SizedBox(height: 8),
      TextField(
        key: const Key('evaluation-target-id'),
        controller: targetIdController,
        decoration: const InputDecoration(
          labelText: '目标 ID',
          helperText:
              'chapter_id、generation_id、revision_id、retrieval_id、session_id 或 project_id',
          border: OutlineInputBorder(),
        ),
      ),
      const SizedBox(height: 8),
      TextField(
        key: const Key('evaluation-project-id'),
        controller: projectIdController,
        decoration: const InputDecoration(
          labelText: '项目 ID（可选筛选 / 引用）',
          border: OutlineInputBorder(),
        ),
      ),
      const SizedBox(height: 8),
      TextField(
        key: const Key('evaluation-chapter-id'),
        controller: chapterIdController,
        decoration: const InputDecoration(
          labelText: '章节 ID（可选引用）',
          border: OutlineInputBorder(),
        ),
      ),
    ],
  );
}
