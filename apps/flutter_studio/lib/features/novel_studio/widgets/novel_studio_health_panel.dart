import 'package:flutter/material.dart';

import '../../../core/ui/app_status_badge.dart';

class NovelStudioHealthPanel extends StatelessWidget {
  const NovelStudioHealthPanel({
    super.key,
    required this.health,
    required this.backendStatus,
    required this.modelLabel,
    required this.adapterLabel,
    required this.runningJobs,
    required this.onRefresh,
  });

  final Map<String, dynamic>? health;
  final String backendStatus;
  final String modelLabel;
  final String adapterLabel;
  final int runningJobs;
  final VoidCallback onRefresh;

  @override
  Widget build(BuildContext context) {
    final status = '${health?['status'] ?? 'unknown'}';
    final tone = switch (status) {
      'ok' => AppStatusTone.success,
      'warning' => AppStatusTone.warning,
      'error' => AppStatusTone.danger,
      _ => AppStatusTone.neutral,
    };
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Text('Health', style: Theme.of(context).textTheme.titleMedium),
                const Spacer(),
                AppStatusBadge(label: status, tone: tone),
              ],
            ),
            const SizedBox(height: 12),
            Text('Backend: $backendStatus'),
            Text('Model: $modelLabel'),
            Text('Adapter: $adapterLabel'),
            Text('Jobs: $runningJobs running'),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: onRefresh,
              icon: const Icon(Icons.refresh),
              label: const Text('Refresh health'),
            ),
          ],
        ),
      ),
    );
  }
}
