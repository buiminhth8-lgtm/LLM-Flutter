import 'package:flutter/material.dart';

import '../models/finetune_log_dto.dart';

class FinetuneLogsPanel extends StatelessWidget {
  const FinetuneLogsPanel({super.key, required this.logs});

  final List<FinetuneLogDto> logs;

  @override
  Widget build(BuildContext context) => Card(
    child: Padding(
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('日志', style: TextStyle(fontWeight: FontWeight.w700)),
          SizedBox(
            height: 160,
            child: ListView(
              children: [
                for (final log in logs)
                  Text('[${log.level}] ${log.step ?? '-'} ${log.message}'),
              ],
            ),
          ),
        ],
      ),
    ),
  );
}
