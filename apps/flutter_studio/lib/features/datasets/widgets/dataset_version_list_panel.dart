import 'package:flutter/material.dart';

import '../models/dataset_version_dto.dart';

class DatasetVersionListPanel extends StatelessWidget {
  const DatasetVersionListPanel({
    super.key,
    required this.versions,
    required this.currentVersionId,
    required this.onSelect,
  });

  final List<DatasetVersionDto> versions;
  final String? currentVersionId;
  final ValueChanged<String> onSelect;

  @override
  Widget build(BuildContext context) {
    if (versions.isEmpty) {
      return const Text('暂无冻结的数据集版本。');
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const Text('数据集版本', style: TextStyle(fontWeight: FontWeight.w700)),
        const SizedBox(height: 6),
        for (final version in versions.take(5))
          ListTile(
            dense: true,
            selected: version.datasetVersionId == currentVersionId,
            title: Text('v${version.version} · ${version.status}'),
            subtitle: Text(
            '训练 ${version.trainSampleCount} / 验证 ${version.valSampleCount} · 警告 ${version.warningCount}',
            ),
            onTap: () => onSelect(version.datasetVersionId),
          ),
      ],
    );
  }
}
