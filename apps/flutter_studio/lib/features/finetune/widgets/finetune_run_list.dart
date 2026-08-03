import 'package:flutter/material.dart';

import '../models/finetune_run_dto.dart';
import 'finetune_status_badge.dart';

class FinetuneRunList extends StatelessWidget {
  const FinetuneRunList({
    super.key,
    required this.runs,
    required this.selectedRunId,
    required this.onSelect,
  });

  final List<FinetuneRunDto> runs;
  final String? selectedRunId;
  final ValueChanged<String> onSelect;

  @override
  Widget build(BuildContext context) => Card(
    child: ListView(
      children: [
        const ListTile(title: Text('Fine-tune Runs')),
        if (runs.isEmpty)
          const ListTile(title: Text('No runs yet.')),
        for (final run in runs)
          ListTile(
            selected: run.runId == selectedRunId,
            title: Text(run.adapterName),
            subtitle: Text(
              '${run.method} · ${run.currentStep}/${run.totalSteps} · ${run.baseModelId}',
            ),
            trailing: FinetuneStatusBadge(status: run.status),
            onTap: () => onSelect(run.runId),
          ),
      ],
    ),
  );
}
