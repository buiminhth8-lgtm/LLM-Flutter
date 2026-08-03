import 'package:flutter/material.dart';

import '../models/dataset_freeze_request_dto.dart';

class DatasetFreezeDialog extends StatefulWidget {
  const DatasetFreezeDialog({super.key, required this.defaultName});

  final String defaultName;

  @override
  State<DatasetFreezeDialog> createState() => _DatasetFreezeDialogState();
}

class _DatasetFreezeDialogState extends State<DatasetFreezeDialog> {
  late final TextEditingController _name;
  final _description = TextEditingController();
  final _valRatio = TextEditingController(text: '0.1');
  final _seed = TextEditingController(text: '42');
  final _threshold = TextEditingController(text: '0.92');
  String _strategy = 'group_by_chapter';
  bool _exactHash = true;
  bool _nearDuplicate = true;

  @override
  void initState() {
    super.initState();
    _name = TextEditingController(text: widget.defaultName);
  }

  @override
  void dispose() {
    _name.dispose();
    _description.dispose();
    _valRatio.dispose();
    _seed.dispose();
    _threshold.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: const Text('冻结数据集版本'),
    content: SizedBox(
      width: 420,
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              key: const Key('dataset-freeze-name'),
              controller: _name,
              decoration: const InputDecoration(labelText: 'name'),
            ),
            TextField(
              controller: _description,
              decoration: const InputDecoration(labelText: 'description'),
            ),
            DropdownButtonFormField<String>(
              initialValue: _strategy,
              decoration: const InputDecoration(labelText: '拆分策略'),
              items: const [
                DropdownMenuItem(
                  value: 'group_by_chapter',
                  child: Text('按章节分组'),
                ),
                DropdownMenuItem(
                  value: 'group_by_project',
                  child: Text('按项目分组'),
                ),
                DropdownMenuItem(
                  value: 'random_by_sample',
                  child: Text('按样本随机'),
                ),
                DropdownMenuItem(value: 'no_validation', child: Text('不使用验证集')),
              ],
              onChanged: (value) =>
                  setState(() => _strategy = value ?? _strategy),
            ),
            TextField(
              controller: _valRatio,
              decoration: const InputDecoration(labelText: 'val_ratio'),
            ),
            TextField(
              controller: _seed,
              decoration: const InputDecoration(labelText: 'seed'),
            ),
            SwitchListTile(
              value: _exactHash,
              title: const Text('精确哈希去重'),
              onChanged: (value) => setState(() => _exactHash = value),
            ),
            SwitchListTile(
              value: _nearDuplicate,
              title: const Text('近似重复警告'),
              onChanged: (value) => setState(() => _nearDuplicate = value),
            ),
            TextField(
              controller: _threshold,
              decoration: const InputDecoration(labelText: '近似重复阈值'),
            ),
          ],
        ),
      ),
    ),
    actions: [
      TextButton(
        onPressed: () => Navigator.of(context).pop(),
        child: const Text('取消'),
      ),
      FilledButton(
        key: const Key('dataset-freeze-submit'),
        onPressed: _submit,
        child: const Text('冻结'),
      ),
    ],
  );

  void _submit() {
    final name = _name.text.trim();
    if (name.isEmpty) {
      return;
    }
    Navigator.of(context).pop(
      DatasetFreezeRequestDto(
        name: name,
        description: _description.text.trim().isEmpty
            ? null
            : _description.text.trim(),
        splitStrategy: _strategy,
        valRatio: double.tryParse(_valRatio.text.trim()) ?? 0.1,
        seed: int.tryParse(_seed.text.trim()) ?? 42,
        exactHash: _exactHash,
        nearDuplicate: _nearDuplicate,
        nearDuplicateThreshold: double.tryParse(_threshold.text.trim()) ?? 0.92,
      ),
    );
  }
}
