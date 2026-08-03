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
      '拆分预览：训练 ${version!.trainSampleCount} / 验证 ${version!.valSampleCount}，已排除重复 ${version!.rejectedDuplicateCount}。',
    );
  }
}
