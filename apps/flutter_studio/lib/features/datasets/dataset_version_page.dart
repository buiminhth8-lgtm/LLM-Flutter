import 'package:flutter/material.dart';

import '../../core/ui/app_section_header.dart';
import 'dataset_controller.dart';
import 'widgets/dataset_dedupe_warning_panel.dart';
import 'widgets/dataset_manifest_panel.dart';
import 'widgets/dataset_split_preview_panel.dart';

class DatasetVersionPage extends StatelessWidget {
  const DatasetVersionPage({super.key, required this.controller});

  final DatasetController controller;

  @override
  Widget build(BuildContext context) => AnimatedBuilder(
    animation: controller,
    builder: (context, _) {
      final state = controller.state;
      final version = state.currentVersion;
      return Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const AppSectionHeader(
              title: '数据集版本',
              subtitle: '为阶段 8 准备的冻结且不可变的数据集产物。',
            ),
            if (version == null)
              const Expanded(child: Center(child: Text('请选择冻结版本。')))
            else
              Expanded(
                child: ListView(
                  children: [
                    Text('v${version.version} · ${version.status}'),
                    DatasetSplitPreviewPanel(version: version),
                    DatasetManifestPanel(
                      version: version,
                      manifest: state.currentManifest,
                    ),
                    DatasetDedupeWarningPanel(warnings: version.warnings),
                  ],
                ),
              ),
          ],
        ),
      );
    },
  );
}
