import 'package:flutter/material.dart';

import '../evaluation_report_page.dart';
import '../models/evaluation_report_dto.dart';

class EvaluationReportPanel extends StatelessWidget {
  const EvaluationReportPanel({
    super.key,
    required this.reports,
    required this.currentReport,
    required this.onGenerate,
    required this.onOpenReport,
  });

  final List<EvaluationReportDto> reports;
  final EvaluationReportDto? currentReport;
  final VoidCallback onGenerate;
  final ValueChanged<String> onOpenReport;

  @override
  Widget build(BuildContext context) => Card(
    child: Padding(
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Text('Reports', style: Theme.of(context).textTheme.titleMedium),
              const Spacer(),
              FilledButton.tonalIcon(
                key: const Key('evaluation-generate-report'),
                onPressed: onGenerate,
                icon: const Icon(Icons.summarize_outlined),
                label: const Text('Generate'),
              ),
            ],
          ),
          const SizedBox(height: 8),
          if (reports.isEmpty)
            const Text('No generated report yet.')
          else
            for (final report in reports.take(5))
              ListTile(
                key: Key('evaluation-report-${report.reportId}'),
                dense: true,
                selected: currentReport?.reportId == report.reportId,
                leading: const Icon(Icons.article_outlined),
                title: Text(report.reportType),
                subtitle: Text(report.summaryText ?? ''),
                onTap: () => onOpenReport(report.reportId),
              ),
          const SizedBox(height: 8),
          Expanded(
            child: currentReport == null
                ? const Center(child: Text('Select or generate a report.'))
                : EvaluationReportPage(report: currentReport!),
          ),
        ],
      ),
    ),
  );
}
