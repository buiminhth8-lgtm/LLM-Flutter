import 'package:flutter/material.dart';

class WritingOutputPanel extends StatelessWidget {
  const WritingOutputPanel({
    super.key,
    required this.output,
    required this.generating,
    required this.saving,
    required this.canSave,
    required this.onStop,
    required this.onSave,
    required this.onAppend,
    this.onEditAsRevision,
    this.onEvaluateGeneration,
  });

  final String output;
  final bool generating;
  final bool saving;
  final bool canSave;
  final VoidCallback onStop;
  final VoidCallback onSave;
  final VoidCallback onAppend;
  final VoidCallback? onEditAsRevision;
  final VoidCallback? onEvaluateGeneration;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('AI 输出', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(width: 12),
          Expanded(
            child: Wrap(
              alignment: WrapAlignment.end,
              spacing: 8,
              runSpacing: 8,
              children: [
                if (generating)
                  OutlinedButton.icon(
                    key: const Key('writing-stop'),
                    onPressed: onStop,
                    icon: const Icon(Icons.stop_circle_outlined),
                    label: const Text('Stop'),
                  ),
                FilledButton.tonal(
                  key: const Key('writing-save-draft'),
                  onPressed: canSave && !saving ? onSave : null,
                  child: const Text('Save to Draft'),
                ),
                OutlinedButton(
                  key: const Key('writing-append-draft'),
                  onPressed: canSave && !saving ? onAppend : null,
                  child: const Text('Append to Draft'),
                ),
                OutlinedButton.icon(
                  key: const Key('writing-edit-revision'),
                  onPressed: canSave && !saving ? onEditAsRevision : null,
                  icon: const Icon(Icons.rate_review_outlined),
                  label: const Text('Edit as Revision'),
                ),
                OutlinedButton.icon(
                  key: const Key('writing-evaluate-generation'),
                  onPressed: canSave && !saving ? onEvaluateGeneration : null,
                  icon: const Icon(Icons.fact_check_outlined),
                  label: const Text('Evaluate'),
                ),
              ],
            ),
          ),
        ],
      ),
      const SizedBox(height: 8),
      Expanded(
        child: Container(
          key: const Key('writing-output'),
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            border: Border.all(color: Theme.of(context).dividerColor),
            borderRadius: BorderRadius.circular(8),
          ),
          child: SingleChildScrollView(
            child: SelectableText(output.isEmpty ? '生成内容会在这里实时显示。' : output),
          ),
        ),
      ),
      const SizedBox(height: 8),
      const Text(
        '阶段 4 保存的是 AI 生成草稿；人工审稿和 Diff 将在阶段 5 实现。',
        style: TextStyle(color: Colors.orange),
      ),
    ],
  );
}
