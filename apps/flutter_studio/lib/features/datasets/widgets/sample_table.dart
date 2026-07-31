import 'package:flutter/material.dart';

import '../models/training_sample_dto.dart';
import 'sample_status_badge.dart';

class SampleTable extends StatelessWidget {
  const SampleTable({
    super.key,
    required this.samples,
    required this.currentSampleId,
    required this.onSelect,
  });

  final List<TrainingSampleDto> samples;
  final String? currentSampleId;
  final ValueChanged<TrainingSampleDto> onSelect;

  @override
  Widget build(BuildContext context) {
    if (samples.isEmpty) {
      return const Center(child: Text('No samples yet.'));
    }
    return ListView(
      key: const Key('sample-table'),
      children: [
        for (final sample in samples)
          Card(
            child: ListTile(
              key: Key('sample-row-${sample.sampleId}'),
              selected: sample.sampleId == currentSampleId,
              leading: SampleStatusBadge(status: sample.status),
              title: Text(
                sample.instruction,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              subtitle: Text(
                '${sample.sampleType} · score ${sample.qualityScore ?? '-'} · revision ${sample.revisionId ?? '-'}',
              ),
              onTap: () => onSelect(sample),
            ),
          ),
      ],
    );
  }
}
