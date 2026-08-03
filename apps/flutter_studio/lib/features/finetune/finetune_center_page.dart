import 'package:flutter/material.dart';

import 'finetune_controller.dart';
import 'finetune_run_detail_page.dart';
import 'models/finetune_run_dto.dart';
import 'widgets/finetune_create_run_dialog.dart';
import 'widgets/finetune_preflight_panel.dart';
import 'widgets/finetune_run_list.dart';

class FinetuneCenterPage extends StatelessWidget {
  const FinetuneCenterPage({
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
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  '微调中心',
                  style: Theme.of(context).textTheme.headlineSmall,
                ),
              ),
              FilledButton.icon(
                key: const Key('finetune-new-run'),
                onPressed: () => showDialog<void>(
                  context: context,
                  builder: (_) => FinetuneCreateRunDialog(
                    preflight: state.preflight,
                    onPreflight: (request) {
                      controller.preflight(request);
                    },
                    onCreate: (request) {
                      Navigator.of(context).maybePop();
                      controller.createRun(request);
                    },
                  ),
                ),
                icon: const Icon(Icons.playlist_add),
                label: const Text('创建任务'),
              ),
              IconButton(
                onPressed: controller.refresh,
                icon: const Icon(Icons.refresh),
              ),
            ],
          ),
          const SizedBox(height: 8),
          if (state.error != null)
            MaterialBanner(
              content: Text(state.error!),
              leading: const Icon(Icons.error_outline),
              actions: const [SizedBox.shrink()],
            ),
          if (state.notice != null)
            Text(state.notice!, style: const TextStyle(color: Colors.green)),
          Expanded(
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                SizedBox(
                  width: 340,
                  child: FinetuneRunList(
                    runs: state.runs,
                    selectedRunId: state.currentRun?.runId,
                    onSelect: controller.selectRun,
                  ),
                ),
                const SizedBox(width: 12),
                SizedBox(
                  width: 320,
                  child: SingleChildScrollView(
                    child: FinetunePreflightPanel(result: state.preflight),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: FinetuneRunDetailPage(
                    controller: controller,
                    onOpenAdapter: onOpenAdapter,
                    onCreateEvaluationSession: onCreateEvaluationSession,
                  ),
                ),
              ],
            ),
          ),
          const Text('阶段 8 训练 LoRA/QLoRA 适配器。适配器评估与基础模型对比属于阶段 9。'),
        ],
      ),
    );
  }
}
