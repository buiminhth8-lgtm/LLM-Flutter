import 'package:flutter/material.dart';

import '../../core/ui/app_status_badge.dart';
import 'novel_studio_route_guard.dart';

class NovelStudioCapabilityBanner extends StatelessWidget {
  const NovelStudioCapabilityBanner({super.key, required this.guard});

  final NovelStudioRouteGuard guard;

  @override
  Widget build(BuildContext context) {
    final ready = [
      'novel_projects',
      'prompt_studio',
      'context_assembler',
      'writing_workspace',
      'revision_system',
      'dataset_builder',
      'finetune_center',
      'adapter_evaluation',
      'novel_rag_memory',
      'full_evaluation_center',
    ].where(guard.isAvailable).length;
    final tone = ready >= 10 ? AppStatusTone.success : AppStatusTone.warning;
    return Card(
      child: ListTile(
        leading: const Icon(Icons.auto_stories_outlined),
        title: const Text('Novel Studio 产品界面'),
        subtitle: Text('后端已暴露 $ready / 10 项工作流能力。'),
        trailing: AppStatusBadge(
          label: ready >= 10 ? '就绪' : '部分可用',
          tone: tone,
        ),
      ),
    );
  }
}
