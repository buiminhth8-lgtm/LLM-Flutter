import 'package:flutter/material.dart';

class RevisionStatusBadge extends StatelessWidget {
  const RevisionStatusBadge({super.key, required this.status});

  final String status;

  @override
  Widget build(BuildContext context) {
    final color = switch (status) {
      'approved' => Colors.green,
      'rejected' => Colors.red,
      'archived' => Colors.grey,
      'reviewing' => Colors.blue,
      _ => Colors.orange,
    };
    final label = switch (status) {
      'draft' => '草稿',
      'reviewing' => '审核中',
      'approved' => '已通过',
      'rejected' => '已拒绝',
      'archived' => '已归档',
      _ => status,
    };
    return Chip(
      avatar: Icon(Icons.circle, color: color, size: 12),
      label: Text(label),
      visualDensity: VisualDensity.compact,
    );
  }
}
