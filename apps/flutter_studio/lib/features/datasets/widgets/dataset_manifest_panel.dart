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
      return const Text('请选择数据集版本查看清单。');
    }
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(10),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '清单 v${version!.version}',
              style: const TextStyle(fontWeight: FontWeight.w700),
            ),
            Text('清单路径：${version!.manifestPath}'),
            Text('训练集：${version!.trainPath}'),
            Text('验证集：${version!.valPath ?? '无'}'),
            Text(
              'Token：训练 ${version!.trainTokenEstimate} / 验证 ${version!.valTokenEstimate}',
            ),
            if (manifest != null)
              Text(
                '拆分：${manifest!.split['strategy'] ?? '-'} · 格式：${manifest!.format}',
              ),
          ],
        ),
      ),
    );
  }
}
