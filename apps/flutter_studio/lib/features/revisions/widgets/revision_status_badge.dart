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
    return Chip(
      avatar: Icon(Icons.circle, color: color, size: 12),
      label: Text(status),
      visualDensity: VisualDensity.compact,
    );
  }
}
