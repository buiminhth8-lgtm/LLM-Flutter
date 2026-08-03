import 'package:flutter/material.dart';
import 'package:flutter_studio/features/finetune/models/finetune_metric_dto.dart';
import 'package:flutter_studio/features/finetune/widgets/finetune_metrics_chart.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('Metrics chart table displays train and val loss', (
    tester,
  ) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: SingleChildScrollView(
            child: FinetuneMetricsChart(
              metrics: [
                FinetuneMetricDto(
                  metricId: 'm1',
                  runId: 'run-1',
                  step: 1,
                  metricType: 'train',
                  metrics: {'train_loss': 2.9, 'learning_rate': 0.0002},
                  createdAt: 'now',
                ),
                FinetuneMetricDto(
                  metricId: 'm2',
                  runId: 'run-1',
                  step: 2,
                  metricType: 'eval',
                  metrics: {'val_loss': 3.1},
                  createdAt: 'now',
                ),
              ],
            ),
          ),
        ),
      ),
    );

    expect(find.text('指标'), findsOneWidget);
    expect(find.text('train'), findsOneWidget);
    expect(find.text('eval'), findsOneWidget);
    expect(find.text('2.9'), findsOneWidget);
    expect(find.text('3.1'), findsOneWidget);
  });
}
