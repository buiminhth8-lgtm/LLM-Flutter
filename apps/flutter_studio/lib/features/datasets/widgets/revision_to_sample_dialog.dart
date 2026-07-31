import 'package:flutter/material.dart';

import '../models/training_dataset_dto.dart';

class RevisionToSampleDialog extends StatefulWidget {
  const RevisionToSampleDialog({
    super.key,
    required this.datasets,
    required this.revisionAccepted,
    required this.revisionApproved,
  });

  final List<TrainingDatasetDto> datasets;
  final bool revisionAccepted;
  final bool revisionApproved;

  @override
  State<RevisionToSampleDialog> createState() => _RevisionToSampleDialogState();
}

class _RevisionToSampleDialogState extends State<RevisionToSampleDialog> {
  String? _datasetId;

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: const Text('Add Revision to Dataset'),
    content: SizedBox(
      width: 420,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          if (!widget.revisionAccepted)
            const Text('Please mark this revision as Dataset Candidate first.'),
          if (!widget.revisionApproved)
            const Text('建议先审核通过该 revision，再创建训练样本。'),
          const SizedBox(height: 8),
          DropdownButtonFormField<String>(
            key: const Key('revision-to-sample-dataset'),
            initialValue: _datasetId,
            decoration: const InputDecoration(
              labelText: 'Dataset',
              border: OutlineInputBorder(),
            ),
            items: [
              for (final dataset in widget.datasets)
                DropdownMenuItem(
                  value: dataset.datasetId,
                  child: Text(dataset.name),
                ),
            ],
            onChanged: widget.revisionAccepted
                ? (value) => setState(() => _datasetId = value)
                : null,
          ),
          const SizedBox(height: 8),
          const Text('sample_type: sft'),
        ],
      ),
    ),
    actions: [
      TextButton(
        onPressed: () => Navigator.of(context).pop(),
        child: const Text('Cancel'),
      ),
      FilledButton(
        key: const Key('revision-to-sample-submit'),
        onPressed: _datasetId == null || !widget.revisionAccepted
            ? null
            : () => Navigator.of(context).pop(_datasetId),
        child: const Text('Create SFT Sample'),
      ),
    ],
  );
}
