import 'package:flutter/material.dart';

import '../models/evaluation_metric_dto.dart';

class EvaluationMetricCards extends StatelessWidget {
  const EvaluationMetricCards({super.key, required this.metrics});

  final List<EvaluationMetricDto> metrics;

  @override
  Widget build(BuildContext context) {
    if (metrics.isEmpty) {
      return const Card(
        child: Padding(
          padding: EdgeInsets.all(16),
          child: Text('No metrics yet. Start or create an evaluation run.'),
        ),
      );
    }
    return Wrap(
      key: const Key('evaluation-metric-cards'),
      spacing: 10,
      runSpacing: 10,
      children: [
        for (final metric in metrics.take(12))
          SizedBox(
            width: 210,
            child: Card(
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      metric.metricName,
                      style: Theme.of(context).textTheme.labelLarge,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 6),
                    Text(
                      metric.metricValue == null
                          ? '-'
                          : metric.metricValue!.toStringAsFixed(2),
                      style: Theme.of(context).textTheme.headlineSmall,
                    ),
                    if (metric.evaluatorType != null)
                      Text(
                        metric.evaluatorType!,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                      ),
                  ],
                ),
              ),
            ),
          ),
      ],
    );
  }
}
