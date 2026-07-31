import 'package:flutter/material.dart';

class RevisionDatasetCandidateToggle extends StatelessWidget {
  const RevisionDatasetCandidateToggle({
    super.key,
    required this.value,
    required this.onChanged,
  });

  final bool value;
  final ValueChanged<bool> onChanged;

  @override
  Widget build(BuildContext context) => SwitchListTile(
    key: const Key('revision-dataset-candidate-toggle'),
    contentPadding: EdgeInsets.zero,
    title: const Text('Dataset candidate'),
    subtitle: const Text('Candidate flag only; no training sample is created.'),
    value: value,
    onChanged: onChanged,
  );
}
