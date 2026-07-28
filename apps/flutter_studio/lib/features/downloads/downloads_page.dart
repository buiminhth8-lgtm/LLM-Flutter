import 'package:flutter/material.dart';

class DownloadsPage extends StatelessWidget {
  const DownloadsPage({
    super.key,
    required this.downloads,
    required this.repoController,
    required this.revisionController,
    required this.onStart,
    required this.onCancel,
    required this.onRetry,
    required this.onRefresh,
  });

  final List<dynamic> downloads;
  final TextEditingController repoController;
  final TextEditingController revisionController;
  final VoidCallback onStart;
  final Future<void> Function(String id) onCancel;
  final Future<void> Function(String id) onRetry;
  final VoidCallback onRefresh;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(children: [
            const Text('Downloads', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
            const Spacer(),
            IconButton.filledTonal(onPressed: onRefresh, icon: const Icon(Icons.refresh), tooltip: 'Refresh'),
          ]),
          const SizedBox(height: 12),
          Row(children: [
            Expanded(child: TextField(controller: repoController, decoration: const InputDecoration(labelText: 'Hugging Face repo_id', border: OutlineInputBorder()))),
            const SizedBox(width: 8),
            SizedBox(width: 220, child: TextField(controller: revisionController, decoration: const InputDecoration(labelText: 'Revision', border: OutlineInputBorder()))),
            const SizedBox(width: 8),
            FilledButton.icon(onPressed: onStart, icon: const Icon(Icons.download), label: const Text('Start')),
          ]),
          const SizedBox(height: 12),
          Expanded(
            child: downloads.isEmpty
                ? const Center(child: Text('No download tasks.'))
                : ListView.separated(
                    itemCount: downloads.length,
                    separatorBuilder: (_, _) => const SizedBox(height: 8),
                    itemBuilder: (context, index) {
                      final map = downloads[index] is Map ? downloads[index] as Map : const {};
                      final id = '${map['job_id'] ?? map['id'] ?? ''}';
                      final total = map['total_bytes'];
                      final downloaded = map['downloaded_bytes'];
                      final progressText = total == null ? 'unknown total' : '$downloaded / $total bytes';
                      return Card(
                        child: ListTile(
                          leading: const Icon(Icons.cloud_download_outlined),
                          title: Text('${map['repo_id'] ?? map['payload']?['repo_id'] ?? 'download'} - ${map['status'] ?? 'unknown'}'),
                          subtitle: Text([
                            progressText,
                            if (map['speed_bytes_per_second'] != null) 'speed: ${map['speed_bytes_per_second']} B/s',
                            if (map['current_file'] != null) 'file: ${map['current_file']}',
                            if (map['message'] != null) '${map['message']}',
                            if (map['error_message'] != null) 'error: ${map['error_message']}',
                          ].join('\n'), maxLines: 5, overflow: TextOverflow.ellipsis),
                          trailing: Wrap(spacing: 8, children: [
                            TextButton(onPressed: id.isEmpty ? null : () => onCancel(id), child: const Text('Cancel')),
                            TextButton(onPressed: id.isEmpty ? null : () => onRetry(id), child: const Text('Retry')),
                          ]),
                        ),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }
}
