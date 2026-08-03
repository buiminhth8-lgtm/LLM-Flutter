import 'package:flutter/material.dart';

class RevisionDatasetCandidateToggle extends StatelessWidget {
  const RevisionDatasetCandidateToggle({
    super.key,
    required this.value,
    required this.onChanged,
  });

  final bool value;
  final ValueChanged<bool> onChanged;

  @override
  Widget build(BuildContext context) => SwitchListTile(
    key: const Key('revision-dataset-candidate-toggle'),
    contentPadding: EdgeInsets.zero,
    title: const Text('数据集候选'),
    subtitle: const Text('仅设置候选标记，不创建训练样本。'),
    value: value,
    onChanged: onChanged,
  );
}
