import 'package:flutter/material.dart';

import '../models/adapter_eval_report_dto.dart';

class AdapterEvalReportPanel extends StatelessWidget {
  const AdapterEvalReportPanel({super.key, required this.reports});

  final List<AdapterEvalReportDto> reports;

  @override
  Widget build(BuildContext context) {
    if (reports.isEmpty) {
      return const Card(
        child: Padding(padding: EdgeInsets.all(12), child: Text('暂无报告。')),
      );
    }
    final report = reports.first;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('评估报告', style: Theme.of(context).textTheme.titleMedium),
            Text('适配器胜出次数：${report.adapterWinCount}'),
            Text('基础模型胜出次数：${report.baseWinCount}'),
            Text('基础模型平均分：${report.averageBaseScore ?? '-'}'),
            Text('适配器平均分：${report.averageAdapterScore ?? '-'}'),
            Text('建议：${report.recommendation}'),
            if (report.summaryText != null) Text(report.summaryText!),
          ],
        ),
      ),
    );
  }
}
