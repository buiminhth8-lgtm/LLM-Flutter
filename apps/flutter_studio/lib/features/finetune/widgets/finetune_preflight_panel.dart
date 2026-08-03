import 'package:flutter/material.dart';

import '../models/finetune_preflight_dto.dart';

class FinetunePreflightPanel extends StatelessWidget {
  const FinetunePreflightPanel({super.key, required this.result});

  final FinetunePreflightDto? result;

  @override
  Widget build(BuildContext context) => Card(
    child: Padding(
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Preflight',
            style: TextStyle(fontWeight: FontWeight.w700),
          ),
          if (result == null)
            const Text('Run preflight before creating a training run.')
          else ...[
            Text(result!.ok ? 'ok=true' : 'ok=false'),
            if (result!.errors.isNotEmpty) ...[
              const SizedBox(height: 6),
              const Text('Errors'),
              for (final error in result!.errors)
                Text('${error['code'] ?? ''}: ${error['message'] ?? ''}'),
            ],
            if (result!.warnings.isNotEmpty) ...[
              const SizedBox(height: 6),
              const Text('Warnings'),
              for (final warning in result!.warnings)
                Text('${warning['code'] ?? ''}: ${warning['message'] ?? ''}'),
            ],
            Text('config: ${result!.resolvedConfig}'),
          ],
        ],
      ),
    ),
  );
}
