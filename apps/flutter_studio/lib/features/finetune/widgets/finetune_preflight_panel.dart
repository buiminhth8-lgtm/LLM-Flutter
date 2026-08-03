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
          const Text('预检', style: TextStyle(fontWeight: FontWeight.w700)),
          if (result == null)
            const Text('创建训练任务前请先运行预检。')
          else ...[
            Text(result!.ok ? 'ok=true' : 'ok=false'),
            if (result!.errors.isNotEmpty) ...[
              const SizedBox(height: 6),
              const Text('错误'),
              for (final error in result!.errors)
                Text('${error['code'] ?? ''}: ${error['message'] ?? ''}'),
            ],
            if (result!.warnings.isNotEmpty) ...[
              const SizedBox(height: 6),
              const Text('警告'),
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
