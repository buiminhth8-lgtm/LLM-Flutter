import 'package:flutter/material.dart';

import '../models/adapter_eval_create_request_dto.dart';

class AdapterEvalCreateSessionDialog extends StatefulWidget {
  const AdapterEvalCreateSessionDialog({super.key, required this.onCreate});

  final ValueChanged<CreateAdapterEvalSessionRequest> onCreate;

  @override
  State<AdapterEvalCreateSessionDialog> createState() =>
      _AdapterEvalCreateSessionDialogState();
}

class _AdapterEvalCreateSessionDialogState
    extends State<AdapterEvalCreateSessionDialog> {
  final _name = TextEditingController(text: '适配器对比');
  final _project = TextEditingController();
  final _run = TextEditingController();
  final _datasetVersion = TextEditingController();
  final _baseModel = TextEditingController(text: 'qwen-local');
  final _adapter = TextEditingController(text: 'adapter-1');

  @override
  void dispose() {
    _name.dispose();
    _project.dispose();
    _run.dispose();
    _datasetVersion.dispose();
    _baseModel.dispose();
    _adapter.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('创建评估会话'),
      content: SizedBox(
        width: 520,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: _name,
              decoration: const InputDecoration(labelText: '名称'),
            ),
            TextField(
              controller: _project,
              decoration: const InputDecoration(labelText: 'project_id（可选）'),
            ),
            TextField(
              controller: _run,
              decoration: const InputDecoration(
                labelText: 'finetune_run_id（可选）',
              ),
            ),
            TextField(
              controller: _datasetVersion,
              decoration: const InputDecoration(
                labelText: 'dataset_version_id（可选）',
              ),
            ),
            TextField(
              controller: _baseModel,
              decoration: const InputDecoration(
                labelText: 'base_model_id（基础模型）',
              ),
            ),
            TextField(
              controller: _adapter,
              decoration: const InputDecoration(labelText: 'adapter_id'),
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('取消'),
        ),
        FilledButton(
          key: const Key('adapter-eval-create-session-submit'),
          onPressed: () {
            widget.onCreate(
              CreateAdapterEvalSessionRequest(
                name: _name.text,
                projectId: _project.text,
                finetuneRunId: _run.text,
                datasetVersionId: _datasetVersion.text,
                baseModelId: _baseModel.text,
                adapterId: _adapter.text,
              ),
            );
            Navigator.pop(context);
          },
          child: const Text('创建'),
        ),
      ],
    );
  }
}
