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
    return Chip(
      label: Text(status),
      visualDensity: VisualDensity.compact,
      side: BorderSide(color: color),
    );
  }
}
