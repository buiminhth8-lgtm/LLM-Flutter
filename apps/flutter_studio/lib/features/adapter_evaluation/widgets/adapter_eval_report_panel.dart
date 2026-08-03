import 'package:flutter/material.dart';

import '../models/adapter_eval_report_dto.dart';

class AdapterEvalReportPanel extends StatelessWidget {
  const AdapterEvalReportPanel({super.key, required this.reports});

  final List<AdapterEvalReportDto> reports;

  @override
  Widget build(BuildContext context) {
    if (reports.isEmpty) {
      return const Card(
        child: Padding(
          padding: EdgeInsets.all(12),
          child: Text('No report yet.'),
        ),
      );
    }
    final report = reports.first;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Evaluation Report',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            Text('adapter_win_count: ${report.adapterWinCount}'),
            Text('base_win_count: ${report.baseWinCount}'),
            Text('average_base_score: ${report.averageBaseScore ?? '-'}'),
            Text('average_adapter_score: ${report.averageAdapterScore ?? '-'}'),
            Text('recommendation: ${report.recommendation}'),
            if (report.summaryText != null) Text(report.summaryText!),
          ],
        ),
      ),
    );
  }
}
