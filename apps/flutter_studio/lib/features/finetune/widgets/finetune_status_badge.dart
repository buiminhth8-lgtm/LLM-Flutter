import 'package:flutter/material.dart';

class FinetuneStatusBadge extends StatelessWidget {
  const FinetuneStatusBadge({super.key, required this.status});

  final String status;

  @override
  Widget build(BuildContext context) {
    final color = switch (status) {
      'completed' => Colors.green,
      'running' => Colors.blue,
      'queued' || 'preflight' || 'saving_checkpoint' => Colors.orange,
      'failed' || 'cancelled' => Colors.red,
      _ => Colors.grey,
    };
    final label = switch (status) {
      'completed' => '已完成',
      'running' => '运行中',
      'queued' => '排队中',
      'preflight' => '预检中',
      'saving_checkpoint' => '保存检查点',
      'failed' => '失败',
      'cancelled' => '已取消',
      'created' => '已创建',
      _ => status,
    };
    return Chip(
      label: Text(label),
      visualDensity: VisualDensity.compact,
      side: BorderSide(color: color),
    );
  }
}
