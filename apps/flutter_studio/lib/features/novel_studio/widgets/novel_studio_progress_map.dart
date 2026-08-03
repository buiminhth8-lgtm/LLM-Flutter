import 'package:flutter/material.dart';

import '../../../core/ui/app_status_badge.dart';
import '../novel_studio_route_guard.dart';

class NovelStudioProgressMap extends StatelessWidget {
  const NovelStudioProgressMap({super.key, required this.guard});

  final NovelStudioRouteGuard guard;

  @override
  Widget build(BuildContext context) {
    final steps = [
      _Step('1. 项目', 'novel_projects'),
      _Step('2. 提示词工作室', 'prompt_studio'),
      _Step('3. 上下文', 'context_assembler'),
      _Step('4. 写作', 'writing_workspace'),
      _Step('5. 修订', 'revision_system'),
      _Step('6. 数据集', 'dataset_builder'),
      _Step('7. 版本 / 配方', 'dataset_versioning'),
      _Step('8. 微调', 'finetune_center'),
      _Step('9. 适配器评估', 'adapter_evaluation'),
      _Step('10. 记忆', 'novel_rag_memory'),
      _Step('11. 评估', 'full_evaluation_center'),
      _Step('12. 产品界面', 'novel_studio_product_ui'),
    ];
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('工作流地图', style: Theme.of(context).textTheme.titleMedium),
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
              label: '数据集 / 训练 / 评估仍需用户显式执行',
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
