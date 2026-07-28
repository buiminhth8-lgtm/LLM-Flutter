import 'package:flutter/material.dart';

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
            const Text('Job Center', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            Expanded(
              child: jobs.isEmpty
                  ? const Center(child: Text('No recent jobs.'))
                  : ListView.separated(
                      itemCount: jobs.length,
                      separatorBuilder: (_, _) => const Divider(height: 1),
                      itemBuilder: (context, index) {
                        final map = jobs[index] is Map ? jobs[index] as Map : const {};
                        final id = '${map['id'] ?? ''}';
                        final status = '${map['status'] ?? 'unknown'}';
                        final progress = map['progress'];
                        final error = map['error_message'];
                        final canCancel = status == 'pending' || status == 'running';
                        return ListTile(
                          dense: true,
                          leading: const Icon(Icons.task_alt_outlined),
                          title: Text('${map['type'] ?? 'job'} - $status'),
                          subtitle: Text([
                            if (progress != null) 'progress: $progress',
                            if (map['message'] != null) '${map['message']}',
                            if (error != null) 'error: $error',
                          ].join('\n'), maxLines: 3, overflow: TextOverflow.ellipsis),
                          trailing: canCancel && onCancel != null && id.isNotEmpty
                              ? TextButton(onPressed: () => onCancel!(id), child: const Text('Cancel'))
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
}
