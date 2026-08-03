import 'package:flutter/material.dart';

import '../models/recipe_recommend_request_dto.dart';
import '../models/training_recipe_dto.dart';
import 'recipe_config_editor.dart';

class TrainingRecipePanel extends StatefulWidget {
  const TrainingRecipePanel({
    super.key,
    required this.recipe,
    required this.onRecommend,
    required this.onSaveConfig,
    required this.onConfirm,
  });

  final TrainingRecipeDto? recipe;
  final ValueChanged<RecipeRecommendRequestDto> onRecommend;
  final ValueChanged<Map<String, Object?>> onSaveConfig;
  final VoidCallback onConfirm;

  @override
  State<TrainingRecipePanel> createState() => _TrainingRecipePanelState();
}

class _TrainingRecipePanelState extends State<TrainingRecipePanel> {
  final _baseModel = TextEditingController(text: 'qwen-local');
  final _vram = TextEditingController(text: '8');
  String _method = 'qlora';
  String _quality = 'balanced';

  @override
  void dispose() {
    _baseModel.dispose();
    _vram.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Card(
    child: Padding(
      padding: const EdgeInsets.all(10),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Text('训练配方预览', style: TextStyle(fontWeight: FontWeight.w700)),
          TextField(
            controller: _baseModel,
            decoration: const InputDecoration(labelText: '基础模型 ID'),
          ),
          DropdownButtonFormField<String>(
            initialValue: _method,
            decoration: const InputDecoration(labelText: 'method'),
            items: const [
              DropdownMenuItem(value: 'qlora', child: Text('QLoRA')),
              DropdownMenuItem(value: 'lora', child: Text('LoRA')),
            ],
            onChanged: (value) => setState(() => _method = value ?? _method),
          ),
          TextField(
            controller: _vram,
            decoration: const InputDecoration(labelText: 'GPU 显存 GB'),
          ),
          DropdownButtonFormField<String>(
            initialValue: _quality,
            decoration: const InputDecoration(labelText: '质量偏好'),
            items: const [
              DropdownMenuItem(value: 'fast', child: Text('快速')),
              DropdownMenuItem(value: 'balanced', child: Text('均衡')),
              DropdownMenuItem(value: 'quality', child: Text('质量优先')),
            ],
            onChanged: (value) => setState(() => _quality = value ?? _quality),
          ),
          FilledButton(
            key: const Key('recipe-recommend'),
            onPressed: () => widget.onRecommend(
              RecipeRecommendRequestDto(
                baseModelId: _baseModel.text.trim().isEmpty
                    ? null
                    : _baseModel.text.trim(),
                method: _method,
                gpuVramGb: double.tryParse(_vram.text.trim()) ?? 8,
                quality: _quality,
              ),
            ),
            child: const Text('推荐配方'),
          ),
          if (widget.recipe != null) ...[
            const SizedBox(height: 8),
            Text('方法：${widget.recipe!.method} · 状态：${widget.recipe!.status}'),
            Text('预计显存：${widget.recipe!.estimatedVramGb ?? '-'} GB'),
            Text('预计耗时：${widget.recipe!.estimatedTrainTimeMinutes ?? '-'} 分钟'),
            Text('配置：${widget.recipe!.recommendedConfig}'),
            RecipeConfigEditor(
              initialConfig: widget.recipe!.recommendedConfig,
              onSave: widget.onSaveConfig,
            ),
            OutlinedButton(
              key: const Key('recipe-confirm'),
              onPressed: widget.recipe!.status == 'confirmed'
                  ? null
                  : widget.onConfirm,
              child: const Text('确认配方'),
            ),
            const Text('确认配方不会启动训练，阶段 8 会使用它。'),
          ],
        ],
      ),
    ),
  );
}
