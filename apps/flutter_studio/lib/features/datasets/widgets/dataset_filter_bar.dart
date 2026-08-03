import 'package:flutter/material.dart';

class DatasetFilterBar extends StatelessWidget {
  const DatasetFilterBar({
    super.key,
    required this.projectController,
    required this.type,
    required this.status,
    required this.onProjectSubmitted,
    required this.onTypeChanged,
    required this.onStatusChanged,
  });

  final TextEditingController projectController;
  final String? type;
  final String? status;
  final ValueChanged<String> onProjectSubmitted;
  final ValueChanged<String?> onTypeChanged;
  final ValueChanged<String?> onStatusChanged;

  @override
  Widget build(BuildContext context) => Column(
    children: [
      TextField(
        controller: projectController,
        decoration: const InputDecoration(
          labelText: '项目筛选',
          border: OutlineInputBorder(),
        ),
        onSubmitted: onProjectSubmitted,
      ),
      const SizedBox(height: 8),
      DropdownButtonFormField<String>(
        initialValue: type,
        decoration: const InputDecoration(
          labelText: '类型',
          border: OutlineInputBorder(),
        ),
        items: const [
          DropdownMenuItem(value: null, child: Text('全部')),
          DropdownMenuItem(value: 'sft', child: Text('sft')),
          DropdownMenuItem(value: 'preference', child: Text('preference')),
          DropdownMenuItem(value: 'mixed', child: Text('mixed')),
        ],
        onChanged: onTypeChanged,
      ),
      const SizedBox(height: 8),
      DropdownButtonFormField<String>(
        initialValue: status,
        decoration: const InputDecoration(
          labelText: '状态',
          border: OutlineInputBorder(),
        ),
        items: const [
          DropdownMenuItem(value: null, child: Text('全部')),
          DropdownMenuItem(value: 'draft', child: Text('draft')),
          DropdownMenuItem(value: 'reviewing', child: Text('reviewing')),
          DropdownMenuItem(value: 'ready', child: Text('ready')),
          DropdownMenuItem(value: 'archived', child: Text('archived')),
        ],
        onChanged: onStatusChanged,
      ),
    ],
  );
}
