import 'package:flutter/material.dart';

import '../models/training_dataset_dto.dart';

class DatasetCreateDialog extends StatefulWidget {
  const DatasetCreateDialog({super.key});

  @override
  State<DatasetCreateDialog> createState() => _DatasetCreateDialogState();
}

class _DatasetCreateDialogState extends State<DatasetCreateDialog> {
  final _name = TextEditingController();
  final _project = TextEditingController();
  final _description = TextEditingController();
  String _type = 'sft';

  @override
  void dispose() {
    _name.dispose();
    _project.dispose();
    _description.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: const Text('Create Dataset'),
    content: SizedBox(
      width: 420,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          TextField(
            key: const Key('dataset-name-input'),
            controller: _name,
            decoration: const InputDecoration(labelText: 'Name'),
          ),
          const SizedBox(height: 8),
          DropdownButtonFormField<String>(
            initialValue: _type,
            decoration: const InputDecoration(labelText: 'Type'),
            items: const [
              DropdownMenuItem(value: 'sft', child: Text('sft')),
              DropdownMenuItem(value: 'preference', child: Text('preference')),
              DropdownMenuItem(value: 'mixed', child: Text('mixed')),
            ],
            onChanged: (value) => setState(() => _type = value ?? 'sft'),
          ),
          const SizedBox(height: 8),
          TextField(
            controller: _project,
            decoration: const InputDecoration(labelText: 'Project ID'),
          ),
          const SizedBox(height: 8),
          TextField(
            controller: _description,
            decoration: const InputDecoration(labelText: 'Description'),
          ),
        ],
      ),
    ),
    actions: [
      TextButton(
        onPressed: () => Navigator.of(context).pop(),
        child: const Text('Cancel'),
      ),
      FilledButton(
        key: const Key('dataset-create-submit'),
        onPressed: () => Navigator.of(context).pop(
          CreateDatasetRequest(
            name: _name.text.trim(),
            type: _type,
            projectId: _project.text.trim().isEmpty
                ? null
                : _project.text.trim(),
            description: _description.text.trim().isEmpty
                ? null
                : _description.text.trim(),
          ),
        ),
        child: const Text('Create'),
      ),
    ],
  );
}
