import 'package:flutter/material.dart';

import '../models/finetune_run_dto.dart';

class FinetuneAdapterResultPanel extends StatelessWidget {
  const FinetuneAdapterResultPanel({
    super.key,
    required this.run,
    required this.onOpenAdapter,
  });

  final FinetuneRunDto? run;
  final VoidCallback onOpenAdapter;

  @override
  Widget build(BuildContext context) => Card(
    child: Padding(
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Adapter Result',
            style: TextStyle(fontWeight: FontWeight.w700),
          ),
          if (run?.adapterId == null)
            const Text('No registered adapter yet.')
          else ...[
            Text('adapter_id: ${run!.adapterId}'),
            Text('path: ${run!.outputAdapterPath ?? '-'}'),
            const Text('Adapter is registered but not auto activated.'),
            OutlinedButton(
              key: const Key('finetune-open-adapter'),
              onPressed: onOpenAdapter,
              child: const Text('Open Adapter'),
            ),
          ],
        ],
      ),
    ),
  );
}
