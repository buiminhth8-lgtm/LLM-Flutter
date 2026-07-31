import 'package:flutter/material.dart';

class WritingModelSelector extends StatelessWidget {
  const WritingModelSelector({
    super.key,
    required this.models,
    required this.value,
    required this.onChanged,
  });

  final List<Map<String, dynamic>> models;
  final String? value;
  final ValueChanged<String?> onChanged;

  @override
  Widget build(BuildContext context) => DropdownButtonFormField<String>(
    key: const Key('writing-model-selector'),
    initialValue: value,
    isExpanded: true,
    items: [
      for (final model in models)
        DropdownMenuItem(
          value: '${model['id'] ?? model['model_id'] ?? ''}',
          child: Text(
            '${model['display_name'] ?? model['name'] ?? model['id'] ?? model['model_id'] ?? ''}',
          ),
        ),
    ],
    onChanged: onChanged,
    decoration: const InputDecoration(
      labelText: '本地模型',
      border: OutlineInputBorder(),
    ),
  );
}
