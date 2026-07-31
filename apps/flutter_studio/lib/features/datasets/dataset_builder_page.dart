import 'dart:async';

import 'package:flutter/material.dart';

import '../../core/ui/app_section_header.dart';
import 'dataset_controller.dart';
import 'dataset_state.dart';
import 'models/training_dataset_dto.dart';
import 'models/training_sample_dto.dart';
import 'widgets/dataset_create_dialog.dart';
import 'widgets/dataset_export_panel.dart';
import 'widgets/dataset_list_panel.dart';
import 'widgets/sample_detail_panel.dart';
import 'widgets/sample_table.dart';

class DatasetBuilderPage extends StatefulWidget {
  const DatasetBuilderPage({super.key, required this.controller});

  final DatasetController controller;

  @override
  State<DatasetBuilderPage> createState() => _DatasetBuilderPageState();
}

class _DatasetBuilderPageState extends State<DatasetBuilderPage> {
  final _projectFilter = TextEditingController();
  final _bulkProject = TextEditingController();
  final _bulkMinScore = TextEditingController(text: '4');

  @override
  void initState() {
    super.initState();
    if (widget.controller.state.datasets.isEmpty) {
      unawaited(widget.controller.refresh());
    }
  }

  @override
  void dispose() {
    _projectFilter.dispose();
    _bulkProject.dispose();
    _bulkMinScore.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AnimatedBuilder(
    animation: widget.controller,
    builder: (context, _) {
      final state = widget.controller.state;
      return Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            AppSectionHeader(
              title: 'Dataset Builder',
              subtitle:
                  'Stage 6：从 approved revision candidates 构建 SFT samples 并导出 draft JSONL。',
              actions: [
                IconButton.filledTonal(
                  onPressed: state.loading ? null : widget.controller.refresh,
                  icon: const Icon(Icons.refresh),
                  tooltip: 'Refresh',
                ),
              ],
            ),
            if (state.loading || state.saving) const LinearProgressIndicator(),
            if (state.error != null)
              MaterialBanner(
                content: Text(state.error!),
                leading: const Icon(Icons.error_outline),
                actions: const [SizedBox.shrink()],
              ),
            if (state.notice != null)
              MaterialBanner(
                content: Text(state.notice!),
                leading: const Icon(Icons.info_outline),
                actions: const [SizedBox.shrink()],
              ),
            const SizedBox(height: 12),
            Expanded(
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  SizedBox(width: 310, child: _buildDatasetPane(state)),
                  const VerticalDivider(width: 24),
                  Expanded(child: _buildSamplesPane(state.samples)),
                  const VerticalDivider(width: 24),
                  SizedBox(width: 370, child: _buildDetailPane(state)),
                ],
              ),
            ),
          ],
        ),
      );
    },
  );

  Widget _buildDatasetPane(DatasetState state) => DatasetListPanel(
    datasets: state.datasets,
    currentDatasetId: state.currentDataset?.datasetId,
    projectController: _projectFilter,
    type: state.selectedType,
    status: state.selectedStatus,
    onProjectSubmitted: (value) => widget.controller.setFilters(
      projectId: value.trim().isEmpty ? null : value.trim(),
      clearProject: value.trim().isEmpty,
    ),
    onTypeChanged: (value) =>
        widget.controller.setFilters(type: value, clearType: value == null),
    onStatusChanged: (value) =>
        widget.controller.setFilters(status: value, clearStatus: value == null),
    onCreate: _showCreateDataset,
    onSelect: widget.controller.selectDataset,
  );

  Widget _buildSamplesPane(List<TrainingSampleDto> samples) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      Row(
        children: [
          const Text(
            'Samples',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700),
          ),
          const Spacer(),
          OutlinedButton.icon(
            key: const Key('dataset-bulk-create'),
            onPressed: widget.controller.state.currentDataset == null
                ? null
                : _bulkCreate,
            icon: const Icon(Icons.playlist_add_outlined),
            label: const Text('Bulk from accepted revisions'),
          ),
        ],
      ),
      const SizedBox(height: 8),
      Expanded(
        child: SampleTable(
          samples: samples,
          currentSampleId: widget.controller.state.currentSample?.sampleId,
          onSelect: widget.controller.selectSample,
        ),
      ),
    ],
  );

  Widget _buildDetailPane(DatasetState state) {
    final dataset = state.currentDataset;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (dataset == null)
          const Expanded(child: Center(child: Text('Select a dataset.')))
        else ...[
          _DatasetSummary(dataset: dataset),
          const SizedBox(height: 12),
          Expanded(
            child: SampleDetailPanel(
              sample: state.currentSample,
              onSave: widget.controller.updateCurrentSample,
              onApprove: widget.controller.approveCurrentSample,
              onReject: (reason) =>
                  widget.controller.rejectCurrentSample(reason: reason),
            ),
          ),
          const Divider(),
          DatasetExportPanel(
            exports: state.exports,
            onExport: () => widget.controller.exportCurrentDataset(),
          ),
        ],
      ],
    );
  }

  Future<void> _showCreateDataset() async {
    final request = await showDialog<CreateDatasetRequest>(
      context: context,
      builder: (_) => const DatasetCreateDialog(),
    );
    if (request != null) {
      await widget.controller.createDataset(request);
    }
  }

  Future<void> _bulkCreate() async {
    final dataset = widget.controller.state.currentDataset;
    if (dataset == null) {
      return;
    }
    final minScore = int.tryParse(_bulkMinScore.text.trim());
    await widget.controller.bulkCreateSamples(
      datasetId: dataset.datasetId,
      projectId: _bulkProject.text.trim().isEmpty
          ? dataset.projectId
          : _bulkProject.text.trim(),
      minScore: minScore,
    );
  }
}

class _DatasetSummary extends StatelessWidget {
  const _DatasetSummary({required this.dataset});

  final TrainingDatasetDto dataset;

  @override
  Widget build(BuildContext context) => Card(
    child: Padding(
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            dataset.name,
            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700),
          ),
          Text('${dataset.type} · ${dataset.status}'),
          Text(
            '${dataset.sampleCount} samples · ${dataset.approvedSampleCount} approved · ${dataset.rejectedSampleCount} rejected',
          ),
        ],
      ),
    ),
  );
}
