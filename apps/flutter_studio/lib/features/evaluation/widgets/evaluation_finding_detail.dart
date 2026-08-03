import 'package:flutter/material.dart';

import '../models/evaluation_finding_dto.dart';

class EvaluationFindingDetail extends StatelessWidget {
  const EvaluationFindingDetail({super.key, required this.finding});

  final EvaluationFindingDto finding;

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: Text(finding.title),
    content: SizedBox(
      width: 560,
      child: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              '${finding.severity} · ${finding.category} · ${finding.status}',
            ),
            const SizedBox(height: 12),
            SelectableText(finding.message),
            if (finding.suggestion != null &&
                finding.suggestion!.trim().isNotEmpty) ...[
              const SizedBox(height: 12),
              Text('建议', style: Theme.of(context).textTheme.titleSmall),
              SelectableText(finding.suggestion!),
            ],
            if (finding.evidence.isNotEmpty) ...[
              const SizedBox(height: 12),
              Text('证据', style: Theme.of(context).textTheme.titleSmall),
              SelectableText(finding.evidence.toString()),
            ],
          ],
        ),
      ),
    ),
    actions: [
      TextButton(
        onPressed: () => Navigator.of(context).pop(),
        child: const Text('关闭'),
      ),
    ],
  );
}
