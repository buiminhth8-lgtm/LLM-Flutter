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
          const Text('适配器结果', style: TextStyle(fontWeight: FontWeight.w700)),
          if (run?.adapterId == null)
            const Text('暂无已注册适配器。')
          else ...[
            Text('适配器 ID：${run!.adapterId}'),
            Text('路径：${run!.outputAdapterPath ?? '-'}'),
            const Text('适配器已注册，但不会自动启用。'),
            OutlinedButton(
              key: const Key('finetune-open-adapter'),
              onPressed: onOpenAdapter,
              child: const Text('打开适配器'),
            ),
          ],
        ],
      ),
    ),
  );
}
