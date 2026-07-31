import 'package:flutter/material.dart';

import '../models/dataset_version_dto.dart';

class DatasetSplitPreviewPanel extends StatelessWidget {
  const DatasetSplitPreviewPanel({super.key, required this.version});

  final DatasetVersionDto? version;

  @override
  Widget build(BuildContext context) {
    if (version == null) {
      return const SizedBox.shrink();
    }
    return Text(
      'Split preview: ${version!.trainSampleCount} train / ${version!.valSampleCount} val, duplicates excluded ${version!.rejectedDuplicateCount}.',
    );
  }
}
