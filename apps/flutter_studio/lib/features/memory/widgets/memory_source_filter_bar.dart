import 'package:flutter/material.dart';

const memorySourceTypeLabels = <String, String>{
  'chapter': '章节',
  'scene': '场景',
  'character': '人物',
  'world_entry': '世界观',
  'plot_thread': '剧情线',
  'timeline_event': '时间线',
  'revision': '修订稿',
  'generation': '生成记录',
  'adapter_eval_result': 'Adapter 结果',
  'manual_note': '手动记忆',
  'foreshadowing': '伏笔',
};

class MemorySourceFilterBar extends StatelessWidget {
  const MemorySourceFilterBar({
    super.key,
    required this.projectController,
    this.sourceType,
    this.status = 'active',
    required this.onApply,
  });

  final TextEditingController projectController;
  final String? sourceType;
  final String status;
  final void Function(String projectId, String? sourceType, String status)
  onApply;

  @override
  Widget build(BuildContext context) => Column(
    children: [
      TextField(
        key: const Key('memory-project-id'),
        controller: projectController,
        decoration: const InputDecoration(
          labelText: '项目 ID',
          border: OutlineInputBorder(),
        ),
        onSubmitted: (_) =>
            onApply(projectController.text.trim(), sourceType, status),
      ),
      const SizedBox(height: 8),
      DropdownButtonFormField<String?>(
        initialValue: sourceType,
        isExpanded: true,
        items: [
          const DropdownMenuItem(value: null, child: Text('全部来源')),
          for (final entry in memorySourceTypeLabels.entries)
            DropdownMenuItem(value: entry.key, child: Text(entry.value)),
        ],
        onChanged: (value) =>
            onApply(projectController.text.trim(), value, status),
        decoration: const InputDecoration(
          labelText: '来源类型',
          border: OutlineInputBorder(),
        ),
      ),
      const SizedBox(height: 8),
      DropdownButtonFormField<String>(
        initialValue: status,
        items: const [
          DropdownMenuItem(value: 'active', child: Text('active')),
          DropdownMenuItem(value: 'stale', child: Text('stale')),
          DropdownMenuItem(value: 'archived', child: Text('archived')),
        ],
        onChanged: (value) => onApply(
          projectController.text.trim(),
          sourceType,
          value ?? 'active',
        ),
        decoration: const InputDecoration(
          labelText: '状态',
          border: OutlineInputBorder(),
        ),
      ),
    ],
  );
}
