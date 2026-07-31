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
      return const Text('No frozen DatasetVersion yet.');
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const Text(
          'Dataset Versions',
          style: TextStyle(fontWeight: FontWeight.w700),
        ),
        const SizedBox(height: 6),
        for (final version in versions.take(5))
          ListTile(
            dense: true,
            selected: version.datasetVersionId == currentVersionId,
            title: Text('v${version.version} · ${version.status}'),
            subtitle: Text(
              '${version.trainSampleCount} train / ${version.valSampleCount} val · ${version.warningCount} warnings',
            ),
            onTap: () => onSelect(version.datasetVersionId),
          ),
      ],
    );
  }
}
