import 'package:flutter/material.dart';

class SampleStatusBadge extends StatelessWidget {
  const SampleStatusBadge({super.key, required this.status});

  final String status;

  @override
  Widget build(BuildContext context) {
    final color = switch (status) {
      'approved' => Colors.green,
      'rejected' => Colors.red,
      'archived' => Colors.grey,
      'exported' => Colors.blue,
      _ => Colors.orange,
    };
    return Chip(
      visualDensity: VisualDensity.compact,
      avatar: Icon(Icons.circle, color: color, size: 12),
      label: Text(status),
    );
  }
}
