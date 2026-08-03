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
      return const Center(child: Text('Select a fine-tune run.'));
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
                Text('run_id: ${run.runId}'),
                Text('dataset_version: ${run.datasetVersionId}'),
                Text('recipe: ${run.recipeId}'),
                Text('base_model: ${run.baseModelId}'),
                Text('method: ${run.method}'),
                Text('progress: ${run.currentStep}/${run.totalSteps}'),
                Text('train_loss: ${run.trainLoss ?? '-'}'),
                Text('val_loss: ${run.valLoss ?? '-'}'),
                Text('best_val_loss: ${run.bestValLoss ?? '-'}'),
                Wrap(
                  spacing: 8,
                  children: [
                    OutlinedButton(
                      key: const Key('finetune-start'),
                      onPressed: run.status == 'created'
                          ? controller.startCurrentRun
                          : null,
                      child: const Text('Start'),
                    ),
                    if (canCancel)
                      OutlinedButton(
                        key: const Key('finetune-cancel'),
                        onPressed: controller.cancelCurrentRun,
                        child: const Text('Cancel'),
                      ),
                    if (canResume)
                      OutlinedButton(
                        key: const Key('finetune-resume-last'),
                        onPressed: controller.resumeCurrentRun,
                        child: const Text('Resume from Last'),
                      ),
                    if (canCreateEvaluation)
                      FilledButton.icon(
                        key: const Key('finetune-create-evaluation-session'),
                        onPressed: () => onCreateEvaluationSession!(run),
                        icon: const Icon(Icons.compare_outlined),
                        label: const Text('Create Evaluation Session'),
                      ),
                  ],
                ),
                Text('config snapshot: ${run.configSnapshot}'),
                Text(
                  'dataset manifest snapshot: ${run.datasetManifestSnapshot}',
                ),
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
