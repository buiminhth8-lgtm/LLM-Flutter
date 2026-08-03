import 'package:flutter/material.dart';

import 'models/evaluation_report_dto.dart';

class EvaluationReportPage extends StatelessWidget {
  const EvaluationReportPage({super.key, required this.report});

  final EvaluationReportDto report;

  @override
  Widget build(BuildContext context) {
    final summary = report.report['summary'];
    final metrics = report.report['metrics'];
    final findings = report.report['findings'];
    final manual = report.report['manual_evaluation'];
    final limitations = report.report['limitations'];
    return ListView(
      key: const Key('evaluation-report-detail'),
      children: [
        Text(report.reportType, style: Theme.of(context).textTheme.titleMedium),
        if (report.summaryText != null) ...[
          const SizedBox(height: 8),
          SelectableText(report.summaryText!),
        ],
        const SizedBox(height: 12),
        _Block(title: 'Summary', value: summary),
        _Block(title: 'Automatic metrics', value: metrics),
        _Block(title: 'Findings', value: findings),
        _Block(title: 'Manual evaluation', value: manual),
        _Block(title: 'Limitations', value: limitations),
      ],
    );
  }
}

class _Block extends StatelessWidget {
  const _Block({required this.title, required this.value});

  final String title;
  final Object? value;

  @override
  Widget build(BuildContext context) => Card(
    child: Padding(
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: Theme.of(context).textTheme.titleSmall),
          const SizedBox(height: 6),
          SelectableText(value == null ? '-' : value.toString()),
        ],
      ),
    ),
  );
}
