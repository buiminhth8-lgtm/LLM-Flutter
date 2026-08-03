import 'package:flutter/material.dart';

class NovelStudioQuickActions extends StatelessWidget {
  const NovelStudioQuickActions({
    super.key,
    required this.onOpenProjects,
    required this.onOpenPrompts,
    required this.onOpenContext,
    required this.onOpenWriting,
    required this.onOpenRevisions,
    required this.onOpenDataset,
    required this.onOpenFinetune,
    required this.onOpenAdapterEvaluation,
    required this.onOpenEvaluation,
    required this.onOpenMemory,
    required this.onOpenDiagnostics,
  });

  final VoidCallback onOpenProjects;
  final VoidCallback onOpenPrompts;
  final VoidCallback onOpenContext;
  final VoidCallback onOpenWriting;
  final VoidCallback onOpenRevisions;
  final VoidCallback onOpenDataset;
  final VoidCallback onOpenFinetune;
  final VoidCallback onOpenAdapterEvaluation;
  final VoidCallback onOpenEvaluation;
  final VoidCallback onOpenMemory;
  final VoidCallback onOpenDiagnostics;

  @override
  Widget build(BuildContext context) {
    final actions = [
      _Action('项目', Icons.library_books_outlined, onOpenProjects),
      _Action('提示词', Icons.description_outlined, onOpenPrompts),
      _Action('上下文', Icons.account_tree_outlined, onOpenContext),
      _Action('写作', Icons.edit_note_outlined, onOpenWriting),
      _Action('修订版本', Icons.rate_review_outlined, onOpenRevisions),
      _Action('数据集', Icons.dataset_outlined, onOpenDataset),
      _Action('微调', Icons.memory_outlined, onOpenFinetune),
      _Action('适配器评估', Icons.compare_outlined, onOpenAdapterEvaluation),
      _Action('记忆', Icons.psychology_alt_outlined, onOpenMemory),
      _Action('评估', Icons.fact_check_outlined, onOpenEvaluation),
      _Action('诊断', Icons.bug_report_outlined, onOpenDiagnostics),
    ];
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: [
        for (final action in actions)
          FilledButton.tonalIcon(
            onPressed: action.onPressed,
            icon: Icon(action.icon),
            label: Text(action.label),
          ),
      ],
    );
  }
}

class _Action {
  const _Action(this.label, this.icon, this.onPressed);

  final String label;
  final IconData icon;
  final VoidCallback onPressed;
}
