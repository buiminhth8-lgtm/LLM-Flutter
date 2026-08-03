import 'package:flutter/material.dart';

import '../models/finetune_create_run_request_dto.dart';
import '../models/finetune_preflight_dto.dart';

class FinetuneCreateRunDialog extends StatefulWidget {
  const FinetuneCreateRunDialog({
    super.key,
    required this.preflight,
    required this.onPreflight,
    required this.onCreate,
  });

  final FinetunePreflightDto? preflight;
  final ValueChanged<FinetunePreflightRequestDto> onPreflight;
  final ValueChanged<FinetuneCreateRunRequestDto> onCreate;

  @override
  State<FinetuneCreateRunDialog> createState() =>
      _FinetuneCreateRunDialogState();
}

class _FinetuneCreateRunDialogState extends State<FinetuneCreateRunDialog> {
  final _datasetVersion = TextEditingController();
  final _recipe = TextEditingController();
  final _baseModel = TextEditingController(text: 'qwen-local');
  final _adapterName = TextEditingController(text: 'novel-adapter-v1');
  bool _startImmediately = true;

  @override
  void dispose() {
    _datasetVersion.dispose();
    _recipe.dispose();
    _baseModel.dispose();
    _adapterName.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: const Text('Create Fine-tune Run'),
    content: SizedBox(
      width: 460,
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              key: const Key('finetune-dataset-version'),
              controller: _datasetVersion,
              decoration: const InputDecoration(
                labelText: 'frozen dataset_version_id',
              ),
            ),
            TextField(
              key: const Key('finetune-recipe'),
              controller: _recipe,
              decoration: const InputDecoration(
                labelText: 'confirmed recipe_id',
              ),
            ),
            TextField(
              key: const Key('finetune-base-model'),
              controller: _baseModel,
              decoration: const InputDecoration(labelText: 'base_model_id'),
            ),
            TextField(
              key: const Key('finetune-adapter-name'),
              controller: _adapterName,
              decoration: const InputDecoration(labelText: 'adapter_name'),
            ),
            SwitchListTile(
              title: const Text('start_immediately'),
              value: _startImmediately,
              onChanged: (value) => setState(() => _startImmediately = value),
            ),
            if (widget.preflight != null)
              Text(
                widget.preflight!.ok
                    ? 'Preflight passed.'
                    : 'Preflight has ${widget.preflight!.errors.length} errors.',
              ),
          ],
        ),
      ),
    ),
    actions: [
      TextButton(
        key: const Key('finetune-preflight'),
        onPressed: () => widget.onPreflight(_request()),
        child: const Text('Preflight'),
      ),
      FilledButton(
        key: const Key('finetune-create-run'),
        onPressed: widget.preflight?.ok == true
            ? () => widget.onCreate(
                FinetuneCreateRunRequestDto(
                  datasetVersionId: _datasetVersion.text.trim(),
                  recipeId: _recipe.text.trim(),
                  baseModelId: _baseModel.text.trim(),
                  adapterName: _adapterName.text.trim(),
                  startImmediately: _startImmediately,
                ),
              )
            : null,
        child: const Text('Create Run'),
      ),
    ],
  );

  FinetunePreflightRequestDto _request() => FinetunePreflightRequestDto(
    datasetVersionId: _datasetVersion.text.trim(),
    recipeId: _recipe.text.trim(),
    baseModelId: _baseModel.text.trim(),
    adapterName: _adapterName.text.trim(),
  );
}
