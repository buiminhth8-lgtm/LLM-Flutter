import 'package:flutter/material.dart';

import '../jobs/jobs_panel.dart';

class StatusPage extends StatelessWidget {
  const StatusPage({
    super.key,
    required this.runtime,
    required this.models,
    required this.gpuScheduler,
    required this.jobs,
    required this.capabilities,
    this.onCancelJob,
  });

  final Map<String, dynamic>? runtime;
  final List<dynamic> models;
  final Map<String, dynamic>? gpuScheduler;
  final List<dynamic> jobs;
  final List<dynamic> capabilities;
  final Future<void> Function(String jobId)? onCancelJob;

  @override
  Widget build(BuildContext context) {
    final data = runtime ?? const <String, dynamic>{};
    return _PagePadding(
      child: ListView(
        children: [
          GridView.count(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            crossAxisCount: MediaQuery.sizeOf(context).width > 1100 ? 4 : 2,
            crossAxisSpacing: 12,
            mainAxisSpacing: 12,
            childAspectRatio: 2.4,
            children: [
              _MetricTile(label: 'CUDA', value: '${data['cuda_available'] ?? 'unknown'}'),
              _MetricTile(label: 'GPU', value: '${data['gpu_name'] ?? 'not detected'}'),
              _MetricTile(label: 'BF16', value: '${data['bf16_supported'] ?? 'unknown'}'),
              _MetricTile(label: 'Models', value: '${models.length}'),
              _MetricTile(label: 'Current model', value: '${data['current_model'] ?? 'none'}'),
              _MetricTile(label: 'Backend', value: '${data['backend'] ?? 'none'}'),
              _MetricTile(label: 'Queue', value: '${data['queue_length'] ?? 0}'),
              _MetricTile(label: 'GPU tasks', value: '${gpuScheduler?['running'] is List ? (gpuScheduler?['running'] as List).length : 0} running'),
            ],
          ),
          const SizedBox(height: 12),
          SizedBox(
            height: 96,
            child: Card(
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: ListView(
                  scrollDirection: Axis.horizontal,
                  children: capabilities.take(12).map((item) {
                    final map = item is Map ? item : const {};
                    return Padding(
                      padding: const EdgeInsets.only(right: 8),
                      child: Chip(label: Text('${map['name'] ?? 'capability'}: ${map['status'] ?? 'unknown'}')),
                    );
                  }).toList(),
                ),
              ),
            ),
          ),
          const SizedBox(height: 12),
          SizedBox(height: 260, child: JobsPanel(jobs: jobs, onCancel: onCancelJob)),
        ],
      ),
    );
  }
}

class _MetricTile extends StatelessWidget {
  const _MetricTile({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(label, style: const TextStyle(color: Colors.black54)),
            const SizedBox(height: 8),
            Text(value, maxLines: 2, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
          ],
        ),
      ),
    );
  }
}

class _PagePadding extends StatelessWidget {
  const _PagePadding({required this.child});
  final Widget child;
  @override
  Widget build(BuildContext context) => Padding(padding: const EdgeInsets.all(20), child: child);
}
