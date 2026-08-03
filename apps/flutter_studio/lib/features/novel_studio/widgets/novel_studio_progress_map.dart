import 'package:flutter/material.dart';

import '../../../core/ui/app_status_badge.dart';
import '../novel_studio_route_guard.dart';

class NovelStudioProgressMap extends StatelessWidget {
  const NovelStudioProgressMap({super.key, required this.guard});

  final NovelStudioRouteGuard guard;

  @override
  Widget build(BuildContext context) {
    final steps = [
      _Step('1. Projects', 'novel_projects'),
      _Step('2. Prompt Studio', 'prompt_studio'),
      _Step('3. Context', 'context_assembler'),
      _Step('4. Writing', 'writing_workspace'),
      _Step('5. Revision', 'revision_system'),
      _Step('6. Dataset', 'dataset_builder'),
      _Step('7. Version/Recipe', 'dataset_versioning'),
      _Step('8. Fine-tune', 'finetune_center'),
      _Step('9. Adapter Eval', 'adapter_evaluation'),
      _Step('10. Memory', 'novel_rag_memory'),
      _Step('11. Evaluation', 'full_evaluation_center'),
      _Step('12. Product UI', 'novel_studio_product_ui'),
    ];
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Workflow map',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 12),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                for (final step in steps)
                  Chip(
                    avatar: Icon(
                      guard.isAvailable(step.capability)
                          ? Icons.check_circle_outline
                          : Icons.lock_outline,
                      size: 18,
                    ),
                    label: Text(step.label),
                    side: BorderSide(
                      color: guard.isAvailable(step.capability)
                          ? Colors.green.shade200
                          : Colors.orange.shade200,
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 12),
            AppStatusBadge(
              label:
                  'Dataset / training / evaluation remain explicit user actions',
              tone: AppStatusTone.info,
            ),
          ],
        ),
      ),
    );
  }
}

class _Step {
  const _Step(this.label, this.capability);

  final String label;
  final String capability;
}
