import 'package:flutter/material.dart';

import '../models/dataset_export_dto.dart';

class DatasetExportPanel extends StatelessWidget {
  const DatasetExportPanel({
    super.key,
    required this.exports,
    required this.onExport,
  });

  final List<DatasetExportDto> exports;
  final VoidCallback onExport;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      FilledButton.icon(
        key: const Key('dataset-export-sft'),
        onPressed: onExport,
        icon: const Icon(Icons.file_download_outlined),
        label: const Text('Export SFT JSONL'),
      ),
      const SizedBox(height: 8),
      Text(
        'Draft export only. DatasetVersion, train/val split, and training are Stage 7+.',
        style: Theme.of(context).textTheme.bodySmall,
      ),
      const Divider(),
      for (final export in exports.take(5))
        ListTile(
          dense: true,
          leading: const Icon(Icons.description_outlined),
          title: Text(
            export.exportPath,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          subtitle: Text('${export.format} · ${export.sampleCount} samples'),
        ),
    ],
  );
}
