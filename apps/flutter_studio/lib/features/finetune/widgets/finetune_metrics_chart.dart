import 'package:flutter/material.dart';

import '../models/finetune_metric_dto.dart';

class FinetuneMetricsChart extends StatelessWidget {
  const FinetuneMetricsChart({super.key, required this.metrics});

  final List<FinetuneMetricDto> metrics;

  @override
  Widget build(BuildContext context) => Card(
    child: Padding(
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Metrics',
            style: TextStyle(fontWeight: FontWeight.w700),
          ),
          const Text('Chart TODO: table view is used in Stage 8 minimum UI.'),
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: DataTable(
              columns: const [
                DataColumn(label: Text('type')),
                DataColumn(label: Text('step')),
                DataColumn(label: Text('train_loss')),
                DataColumn(label: Text('val_loss')),
                DataColumn(label: Text('lr')),
              ],
              rows: [
                for (final metric in metrics)
                  DataRow(
                    cells: [
                      DataCell(Text(metric.metricType)),
                      DataCell(Text('${metric.step}')),
                      DataCell(Text('${metric.trainLoss ?? '-'}')),
                      DataCell(Text('${metric.valLoss ?? '-'}')),
                      DataCell(
                        Text('${metric.metrics['learning_rate'] ?? '-'}'),
                      ),
                    ],
                  ),
              ],
            ),
          ),
        ],
      ),
    ),
  );
}
