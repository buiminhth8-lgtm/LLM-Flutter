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
          const Text('检查点', style: TextStyle(fontWeight: FontWeight.w700)),
          for (final checkpoint in checkpoints)
            ListTile(
              dense: true,
              title: Text(
                '${_checkpointTypeLabel(checkpoint.checkpointType)} 步数 ${checkpoint.step}'
                '${checkpoint.isBest ? ' · 最佳' : ''}'
                '${checkpoint.isLast ? ' · 最近' : ''}',
              ),
              subtitle: Text(checkpoint.checkpointPath),
              trailing: TextButton(
                onPressed: () => onResumeCheckpoint(checkpoint.checkpointId),
                child: const Text('恢复'),
              ),
            ),
        ],
      ),
    ),
  );

  String _checkpointTypeLabel(String value) => switch (value) {
    'best' => '最佳检查点',
    'last' => '最近检查点',
    _ => value,
  };
}
