import 'package:flutter/material.dart';

class DatasetDedupeWarningPanel extends StatelessWidget {
  const DatasetDedupeWarningPanel({super.key, required this.warnings});

  final List<Map<String, dynamic>> warnings;

  @override
  Widget build(BuildContext context) {
    if (warnings.isEmpty) {
      return const Text('No dedupe warnings.');
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Warnings', style: TextStyle(fontWeight: FontWeight.w700)),
        for (final warning in warnings.take(4))
          Text('• ${warning['code']}: ${warning['message'] ?? ''}'),
      ],
    );
  }
}
