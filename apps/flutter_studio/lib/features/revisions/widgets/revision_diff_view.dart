import 'package:flutter/material.dart';

import '../models/revision_diff_dto.dart';

class RevisionDiffView extends StatelessWidget {
  const RevisionDiffView({super.key, required this.diff});

  final RevisionDiffDto diff;

  @override
  Widget build(BuildContext context) {
    final summary = diff.summary;
    return DecoratedBox(
      decoration: BoxDecoration(
        border: Border.all(color: Theme.of(context).dividerColor),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Padding(
            padding: const EdgeInsets.all(10),
            child: Wrap(
              spacing: 12,
              runSpacing: 8,
              children: [
                _Metric(label: 'Original', value: summary.originalChars),
                _Metric(label: 'Edited', value: summary.editedChars),
                _Metric(label: 'Added', value: summary.addedChars),
                _Metric(label: 'Removed', value: summary.removedChars),
                _Metric(label: 'Blocks', value: summary.changedBlocks),
              ],
            ),
          ),
          const Divider(height: 1),
          Expanded(
            child: ListView.builder(
              key: const Key('revision-diff-view'),
              padding: const EdgeInsets.all(10),
              itemCount: diff.ops.length,
              itemBuilder: (context, index) {
                final op = diff.ops[index];
                return _DiffOpTile(op: op);
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _Metric extends StatelessWidget {
  const _Metric({required this.label, required this.value});

  final String label;
  final int value;

  @override
  Widget build(BuildContext context) =>
      Chip(label: Text('$label: $value'), visualDensity: VisualDensity.compact);
}

class _DiffOpTile extends StatelessWidget {
  const _DiffOpTile({required this.op});

  final RevisionDiffOpDto op;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final color = switch (op.type) {
      'insert' => Colors.green.shade50,
      'delete' => Colors.red.shade50,
      _ => scheme.surface,
    };
    final icon = switch (op.type) {
      'insert' => Icons.add_circle_outline,
      'delete' => Icons.remove_circle_outline,
      _ => Icons.drag_handle,
    };
    final prefix = switch (op.type) {
      'insert' => '+ ',
      'delete' => '- ',
      _ => '  ',
    };
    return Container(
      margin: const EdgeInsets.only(bottom: 6),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: Theme.of(context).dividerColor),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, size: 18),
          const SizedBox(width: 8),
          Expanded(child: SelectableText('$prefix${op.text}')),
        ],
      ),
    );
  }
}
