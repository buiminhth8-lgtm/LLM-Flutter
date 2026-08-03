import 'package:flutter/material.dart';

class RecipeConfigEditor extends StatefulWidget {
  const RecipeConfigEditor({
    super.key,
    required this.initialConfig,
    required this.onSave,
  });

  final Map<String, dynamic> initialConfig;
  final ValueChanged<Map<String, Object?>> onSave;

  @override
  State<RecipeConfigEditor> createState() => _RecipeConfigEditorState();
}

class _RecipeConfigEditorState extends State<RecipeConfigEditor> {
  late final TextEditingController _epochs;
  late final TextEditingController _learningRate;

  @override
  void initState() {
    super.initState();
    _epochs = TextEditingController(
      text: '${widget.initialConfig['epochs'] ?? 3}',
    );
    _learningRate = TextEditingController(
      text: '${widget.initialConfig['learning_rate'] ?? 0.0002}',
    );
  }

  @override
  void dispose() {
    _epochs.dispose();
    _learningRate.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      TextField(
        key: const Key('recipe-epochs'),
        controller: _epochs,
        decoration: const InputDecoration(labelText: 'epochs'),
      ),
      TextField(
        controller: _learningRate,
        decoration: const InputDecoration(labelText: 'learning_rate'),
      ),
      const SizedBox(height: 6),
      OutlinedButton(
        key: const Key('recipe-config-save'),
        onPressed: () => widget.onSave({
          'user_config': {
            'epochs': int.tryParse(_epochs.text.trim()) ?? 3,
            'learning_rate':
                double.tryParse(_learningRate.text.trim()) ?? 0.0002,
          },
        }),
        child: const Text('保存配方配置'),
      ),
    ],
  );
}
