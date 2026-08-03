import 'package:flutter/material.dart';

import 'finetune_controller.dart';
import 'models/finetune_run_dto.dart';
import 'widgets/finetune_adapter_result_panel.dart';
import 'widgets/finetune_checkpoint_panel.dart';
import 'widgets/finetune_logs_panel.dart';
import 'widgets/finetune_metrics_chart.dart';
import 'widgets/finetune_status_badge.dart';

class FinetuneRunDetailPage extends StatelessWidget {
  const FinetuneRunDetailPage({
    super.key,
    required this.controller,
    required this.onOpenAdapter,
    this.onCreateEvaluationSession,
  });

  final FinetuneController controller;
  final VoidCallback onOpenAdapter;
  final ValueChanged<FinetuneRunDto>? onCreateEvaluationSession;

  @override
  Widget build(BuildContext context) {
    final state = controller.state;
    final run = state.currentRun;
    if (run == null) {
      return const Center(child: Text('请选择微调任务。'));
    }
    final canCancel = !{
      'completed',
      'failed',
      'cancelled',
    }.contains(run.status);
    final canResume =
        {'failed', 'cancelled'}.contains(run.status) &&
        run.lastCheckpointId != null;
    final canCreateEvaluation =
        run.status == 'completed' &&
        run.adapterId != null &&
        run.adapterId!.isNotEmpty &&
        onCreateEvaluationSession != null;
    return ListView(
      padding: const EdgeInsets.all(12),
      children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        run.adapterName,
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                    ),
                    FinetuneStatusBadge(status: run.status),
                  ],
                ),
                Text('运行 ID：${run.runId}'),
                Text('数据集版本：${run.datasetVersionId}'),
                Text('配方：${run.recipeId}'),
                Text('基础模型：${run.baseModelId}'),
                Text('方法：${run.method}'),
                Text('进度：${run.currentStep}/${run.totalSteps}'),
                Text('训练 loss：${run.trainLoss ?? '-'}'),
                Text('验证 loss：${run.valLoss ?? '-'}'),
                Text('最佳验证 loss：${run.bestValLoss ?? '-'}'),
                Wrap(
                  spacing: 8,
                  children: [
                    OutlinedButton(
                      key: const Key('finetune-start'),
                      onPressed: run.status == 'created'
                          ? controller.startCurrentRun
                          : null,
                      child: const Text('开始'),
                    ),
                    if (canCancel)
                      OutlinedButton(
                        key: const Key('finetune-cancel'),
                        onPressed: controller.cancelCurrentRun,
                        child: const Text('取消'),
                      ),
                    if (canResume)
                      OutlinedButton(
                        key: const Key('finetune-resume-last'),
                        onPressed: controller.resumeCurrentRun,
                        child: const Text('从最近检查点恢复'),
                      ),
                    if (canCreateEvaluation)
                      FilledButton.icon(
                        key: const Key('finetune-create-evaluation-session'),
                        onPressed: () => onCreateEvaluationSession!(run),
                        icon: const Icon(Icons.compare_outlined),
                        label: const Text('创建评估会话'),
                      ),
                  ],
                ),
                Text('配置快照：${run.configSnapshot}'),
                Text('数据集清单快照：${run.datasetManifestSnapshot}'),
              ],
            ),
          ),
        ),
        FinetuneMetricsChart(metrics: state.metrics),
        FinetuneLogsPanel(logs: state.logs),
        FinetuneCheckpointPanel(
          checkpoints: state.checkpoints,
          onResumeCheckpoint: (id) =>
              controller.resumeCurrentRun(checkpointId: id),
        ),
        FinetuneAdapterResultPanel(run: run, onOpenAdapter: onOpenAdapter),
      ],
    );
  }
}
