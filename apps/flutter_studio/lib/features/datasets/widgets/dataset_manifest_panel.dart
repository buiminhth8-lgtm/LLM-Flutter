import 'package:flutter/material.dart';

import '../models/dataset_manifest_dto.dart';
import '../models/dataset_version_dto.dart';

class DatasetManifestPanel extends StatelessWidget {
  const DatasetManifestPanel({
    super.key,
    required this.version,
    required this.manifest,
  });

  final DatasetVersionDto? version;
  final DatasetManifestDto? manifest;

  @override
  Widget build(BuildContext context) {
    if (version == null) {
      return const Text('Select a DatasetVersion to view manifest.');
    }
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(10),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Manifest v${version!.version}',
              style: const TextStyle(fontWeight: FontWeight.w700),
            ),
            Text('manifest: ${version!.manifestPath}'),
            Text('train: ${version!.trainPath}'),
            Text('val: ${version!.valPath ?? 'none'}'),
            Text(
              'tokens: ${version!.trainTokenEstimate} train / ${version!.valTokenEstimate} val',
            ),
            if (manifest != null)
              Text(
                'split: ${manifest!.split['strategy'] ?? '-'} · format: ${manifest!.format}',
              ),
          ],
        ),
      ),
    );
  }
}
