import 'package:flutter/material.dart';

import '../models/finetune_checkpoint_dto.dart';

class FinetuneCheckpointPanel extends StatelessWidget {
  const FinetuneCheckpointPanel({
    super.key,
    required this.checkpoints,
    required this.onResumeCheckpoint,
  });

  final List<FinetuneCheckpointDto> checkpoints;
  final ValueChanged<String> onResumeCheckpoint;

  @override
  Widget build(BuildContext context) => Card(
    child: Padding(
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Checkpoints',
            style: TextStyle(fontWeight: FontWeight.w700),
          ),
          for (final checkpoint in checkpoints)
            ListTile(
              dense: true,
              title: Text(
                '${checkpoint.checkpointType} step ${checkpoint.step}'
                '${checkpoint.isBest ? ' · best' : ''}'
                '${checkpoint.isLast ? ' · last' : ''}',
              ),
              subtitle: Text(checkpoint.checkpointPath),
              trailing: TextButton(
                onPressed: () => onResumeCheckpoint(checkpoint.checkpointId),
                child: const Text('Resume'),
              ),
            ),
        ],
      ),
    ),
  );
}
