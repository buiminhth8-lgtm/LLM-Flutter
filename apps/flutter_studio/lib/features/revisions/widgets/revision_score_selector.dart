import 'package:flutter/material.dart';

import '../models/revision_score.dart';

class RevisionScoreSelector extends StatelessWidget {
  const RevisionScoreSelector({
    super.key,
    required this.value,
    required this.onChanged,
  });

  final int? value;
  final ValueChanged<int?> onChanged;

  @override
  Widget build(BuildContext context) => DropdownButtonFormField<int>(
    key: const Key('revision-score-selector'),
    initialValue: value,
    isExpanded: true,
    decoration: const InputDecoration(
      labelText: '用户评分',
      border: OutlineInputBorder(),
    ),
    items: [
      const DropdownMenuItem<int>(value: null, child: Text('暂无评分')),
      for (final score in revisionScores)
        DropdownMenuItem<int>(value: score.value, child: Text(score.label)),
    ],
    onChanged: onChanged,
  );
}
