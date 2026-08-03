import 'package:flutter/material.dart';

import '../models/training_dataset_dto.dart';
import 'dataset_filter_bar.dart';

class DatasetListPanel extends StatelessWidget {
  const DatasetListPanel({
    super.key,
    required this.datasets,
    required this.currentDatasetId,
    required this.projectController,
    required this.type,
    required this.status,
    required this.onProjectSubmitted,
    required this.onTypeChanged,
    required this.onStatusChanged,
    required this.onCreate,
    required this.onSelect,
  });

  final List<TrainingDatasetDto> datasets;
  final String? currentDatasetId;
  final TextEditingController projectController;
  final String? type;
  final String? status;
  final ValueChanged<String> onProjectSubmitted;
  final ValueChanged<String?> onTypeChanged;
  final ValueChanged<String?> onStatusChanged;
  final VoidCallback onCreate;
  final ValueChanged<String> onSelect;

  @override
  Widget build(BuildContext context) => ListView(
    children: [
      FilledButton.icon(
        key: const Key('dataset-create-button'),
        onPressed: onCreate,
        icon: const Icon(Icons.add),
        label: const Text('新建数据集'),
      ),
      const SizedBox(height: 12),
      DatasetFilterBar(
        projectController: projectController,
        type: type,
        status: status,
        onProjectSubmitted: onProjectSubmitted,
        onTypeChanged: onTypeChanged,
        onStatusChanged: onStatusChanged,
      ),
      const SizedBox(height: 12),
      for (final dataset in datasets)
        ListTile(
          key: Key('dataset-row-${dataset.datasetId}'),
          selected: dataset.datasetId == currentDatasetId,
          leading: const Icon(Icons.dataset_outlined),
          title: Text(
            dataset.name,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          subtitle: Text(
            '${dataset.type} · ${datasetStatusLabel(dataset.status)} · ${dataset.sampleCount} 个样本',
          ),
          onTap: () => onSelect(dataset.datasetId),
        ),
    ],
  );
}

String datasetStatusLabel(String value) => switch (value) {
  'draft' => '草稿',
  'ready' => '可冻结',
  'dirty' => '已变更',
  'frozen' => '已冻结',
  'archived' => '已归档',
  _ => value,
};
