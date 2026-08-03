import 'package:flutter/material.dart';

import 'evaluation_controller.dart';
import 'models/evaluation_run_dto.dart';
import 'widgets/evaluation_findings_table.dart';
import 'widgets/evaluation_manual_score_panel.dart';
import 'widgets/evaluation_metric_cards.dart';
import 'widgets/evaluation_report_panel.dart';

class EvaluationRunDetailPage extends StatelessWidget {
  const EvaluationRunDetailPage({super.key, required this.controller});

  final EvaluationController controller;

  @override
  Widget build(BuildContext context) {
    final state = controller.state;
    final run = state.currentRun;
    if (run == null) {
      return const Center(child: Text('请选择评估运行。'));
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _RunHeader(
          run: run,
          onStart: controller.startCurrentRun,
          onCancel: controller.cancelCurrentRun,
          onArchive: controller.archiveCurrentRun,
        ),
        const SizedBox(height: 8),
        Expanded(
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Expanded(
                flex: 3,
                child: ListView(
                  key: const Key('evaluation-run-detail-scroll'),
                  children: [
                    EvaluationMetricCards(metrics: state.metrics),
                    const SizedBox(height: 8),
                    SizedBox(
                      height: 440,
                      child: EvaluationFindingsTable(
                        findings: state.findings,
                        onStatusChanged: controller.updateFindingStatus,
                      ),
                    ),
                  ],
                ),
              ),
              const VerticalDivider(width: 20),
              SizedBox(
                width: 410,
                child: Column(
                  children: [
                    EvaluationManualScorePanel(
                      scores: state.manualScores,
                      onSave: controller.addManualScore,
                    ),
                    const SizedBox(height: 8),
                    Expanded(
                      child: EvaluationReportPanel(
                        reports: state.reports,
                        currentReport: state.currentReport,
                        onGenerate: controller.generateReport,
                        onOpenReport: controller.openReport,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _RunHeader extends StatelessWidget {
  const _RunHeader({
    required this.run,
    required this.onStart,
    required this.onCancel,
    required this.onArchive,
  });

  final EvaluationRunDto run;
  final VoidCallback onStart;
  final VoidCallback onCancel;
  final VoidCallback onArchive;

  @override
  Widget build(BuildContext context) => Card(
    child: Padding(
      padding: const EdgeInsets.all(12),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(run.name, style: Theme.of(context).textTheme.titleMedium),
                Text(
                  '${run.targetType} ${run.targetId} · ${run.status} · ${run.summaryText ?? '暂无摘要'}',
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
                const Text('自动评估仅供参考，不会修改小说正文或训练数据。'),
              ],
            ),
          ),
          Text(
            run.overallScore == null
                ? '-'
                : run.overallScore!.toStringAsFixed(1),
            style: Theme.of(context).textTheme.headlineMedium,
          ),
          const SizedBox(width: 12),
          OutlinedButton(
            key: const Key('evaluation-start-run'),
            onPressed: run.status == 'completed' ? null : onStart,
            child: const Text('开始'),
          ),
          const SizedBox(width: 8),
          OutlinedButton(
            key: const Key('evaluation-cancel-run'),
            onPressed: {'running', 'queued', 'created'}.contains(run.status)
                ? onCancel
                : null,
            child: const Text('取消'),
          ),
          const SizedBox(width: 8),
          IconButton(
            key: const Key('evaluation-archive-run'),
            onPressed: onArchive,
            icon: const Icon(Icons.archive_outlined),
            tooltip: '归档',
          ),
        ],
      ),
    ),
  );
}
