import 'package:flutter/material.dart';

import '../models/evaluation_run_dto.dart';

class EvaluationRunList extends StatelessWidget {
  const EvaluationRunList({
    super.key,
    required this.runs,
    this.currentRunId,
    required this.onSelect,
  });

  final List<EvaluationRunDto> runs;
  final String? currentRunId;
  final ValueChanged<String> onSelect;

  @override
  Widget build(BuildContext context) {
    if (runs.isEmpty) {
      return const Center(child: Text('暂无评估运行。'));
    }
    return ListView.builder(
      key: const Key('evaluation-run-list'),
      itemCount: runs.length,
      itemBuilder: (context, index) {
        final run = runs[index];
        return ListTile(
          key: Key('evaluation-run-${run.runId}'),
          selected: run.runId == currentRunId,
          leading: Icon(_statusIcon(run.status)),
          title: Text(run.name, maxLines: 1, overflow: TextOverflow.ellipsis),
          subtitle: Text(
            '${run.targetType} · ${run.status} · ${_score(run.overallScore)}',
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          onTap: () => onSelect(run.runId),
        );
      },
    );
  }

  static IconData _statusIcon(String status) => switch (status) {
    'completed' => Icons.verified_outlined,
    'failed' => Icons.error_outline,
    'cancelled' => Icons.stop_circle_outlined,
    'running' || 'queued' => Icons.pending_outlined,
    'archived' => Icons.archive_outlined,
    _ => Icons.fact_check_outlined,
  };

  static String _score(double? score) =>
      score == null ? '暂无评分' : '评分 ${score.toStringAsFixed(1)}';
}
