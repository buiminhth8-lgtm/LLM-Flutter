import 'package:flutter/material.dart';

import '../../core/ui/app_empty_state.dart';
import '../../core/ui/app_progress_bar.dart';
import '../../core/ui/app_status_badge.dart';

class JobsPanel extends StatelessWidget {
  const JobsPanel({super.key, required this.jobs, this.onCancel});

  final List<dynamic> jobs;
  final Future<void> Function(String jobId)? onCancel;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              '任务中心',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 8),
            Expanded(
              child: jobs.isEmpty
                  ? const AppEmptyState(
                      title: '没有最近任务',
                      icon: Icons.task_alt_outlined,
                    )
                  : ListView.separated(
                      itemCount: jobs.length,
                      separatorBuilder: (_, _) => const Divider(height: 1),
                      itemBuilder: (context, index) {
                        final map = jobs[index] is Map
                            ? jobs[index] as Map
                            : const {};
                        final id = '${map['id'] ?? ''}';
                        final status = '${map['status'] ?? 'unknown'}';
                        final progress = map['progress'] is num
                            ? (map['progress'] as num).toDouble().clamp(
                                0.0,
                                1.0,
                              )
                            : null;
                        final errorCode = map['error_code'];
                        final error = map['error_message'];
                        final canCancel =
                            status == 'pending' || status == 'running';
                        return ListTile(
                          dense: true,
                          leading: const Icon(Icons.task_alt_outlined),
                          title: Row(
                            children: [
                              Expanded(child: Text('${map['type'] ?? 'job'}')),
                              AppStatusBadge(
                                label: status,
                                tone: _tone(status),
                              ),
                            ],
                          ),
                          subtitle: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              if (progress != null)
                                AppProgressBar(
                                  value: progress,
                                  label:
                                      '${(progress * 100).toStringAsFixed(1)}%',
                                ),
                              if (map['message'] != null)
                                Text('${map['message']}'),
                              if (errorCode != null || error != null)
                                Text(
                                  '${errorCode ?? 'ERROR'}: ${error ?? ''}',
                                  maxLines: 2,
                                  overflow: TextOverflow.ellipsis,
                                  style: TextStyle(
                                    color: Theme.of(context).colorScheme.error,
                                  ),
                                ),
                            ],
                          ),
                          trailing:
                              canCancel && onCancel != null && id.isNotEmpty
                              ? TextButton(
                                  onPressed: () => onCancel!(id),
                                  child: const Text('取消'),
                                )
                              : null,
                        );
                      },
                    ),
            ),
          ],
        ),
      ),
    );
  }

  AppStatusTone _tone(String status) {
    return switch (status) {
      'succeeded' => AppStatusTone.success,
      'failed' => AppStatusTone.danger,
      'cancelled' => AppStatusTone.warning,
      'running' || 'pending' || 'cancelling' => AppStatusTone.info,
      _ => AppStatusTone.neutral,
    };
  }
}
