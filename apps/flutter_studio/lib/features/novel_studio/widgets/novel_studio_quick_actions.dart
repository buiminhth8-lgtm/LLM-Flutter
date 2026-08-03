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
      _Action('Projects', Icons.library_books_outlined, onOpenProjects),
      _Action('Prompts', Icons.description_outlined, onOpenPrompts),
      _Action('Context', Icons.account_tree_outlined, onOpenContext),
      _Action('Writing', Icons.edit_note_outlined, onOpenWriting),
      _Action('Revision', Icons.rate_review_outlined, onOpenRevisions),
      _Action('Dataset', Icons.dataset_outlined, onOpenDataset),
      _Action('Fine-tune', Icons.memory_outlined, onOpenFinetune),
      _Action('Adapter Eval', Icons.compare_outlined, onOpenAdapterEvaluation),
      _Action('Memory', Icons.psychology_alt_outlined, onOpenMemory),
      _Action('Evaluation', Icons.fact_check_outlined, onOpenEvaluation),
      _Action('Diagnostics', Icons.bug_report_outlined, onOpenDiagnostics),
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
