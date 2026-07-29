import 'package:flutter/material.dart';

import '../../core/models/dto.dart';
import '../../core/utils/formatters.dart';

class DownloadsPage extends StatelessWidget {
  const DownloadsPage({
    super.key,
    required this.downloads,
    required this.repoController,
    required this.revisionController,
    required this.allowPatternsController,
    required this.ignorePatternsController,
    required this.onStart,
    required this.onCancel,
    required this.onRetry,
    required this.onViewModel,
    required this.onRefresh,
  });

  final List<DownloadTaskDto> downloads;
  final TextEditingController repoController;
  final TextEditingController revisionController;
  final TextEditingController allowPatternsController;
  final TextEditingController ignorePatternsController;
  final VoidCallback onStart;
  final Future<void> Function(String id) onCancel;
  final Future<void> Function(String id) onRetry;
  final Future<void> Function(String modelId) onViewModel;
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
            SizedBox(width: 180, child: TextField(controller: revisionController, decoration: const InputDecoration(labelText: 'Revision', border: OutlineInputBorder()))),
            const SizedBox(width: 8),
            FilledButton.icon(onPressed: onStart, icon: const Icon(Icons.download), label: const Text('Start')),
          ]),
          const SizedBox(height: 8),
          Row(children: [
            Expanded(child: TextField(controller: allowPatternsController, decoration: const InputDecoration(labelText: 'Allow patterns, comma separated', border: OutlineInputBorder()))),
            const SizedBox(width: 8),
            Expanded(child: TextField(controller: ignorePatternsController, decoration: const InputDecoration(labelText: 'Ignore patterns, comma separated', border: OutlineInputBorder()))),
          ]),
          const SizedBox(height: 12),
          Expanded(
            child: downloads.isEmpty
                ? const Center(child: Text('No download tasks.'))
                : ListView.separated(
                    itemCount: downloads.length,
                    separatorBuilder: (_, _) => const SizedBox(height: 8),
                    itemBuilder: (context, index) => _DownloadCard(
                      task: downloads[index],
                      onCancel: onCancel,
                      onRetry: onRetry,
                      onViewModel: onViewModel,
                    ),
                  ),
          ),
        ],
      ),
    );
  }
}

class _DownloadCard extends StatelessWidget {
  const _DownloadCard({
    required this.task,
    required this.onCancel,
    required this.onRetry,
    required this.onViewModel,
  });

  final DownloadTaskDto task;
  final Future<void> Function(String id) onCancel;
  final Future<void> Function(String id) onRetry;
  final Future<void> Function(String modelId) onViewModel;

  @override
  Widget build(BuildContext context) {
    final hasPercent = task.percent != null;
    final progressValue = hasPercent ? (task.percent! / 100).clamp(0.0, 1.0) : null;
    final totalText = task.totalBytes == null ? '总大小未知' : formatBytes(task.totalBytes);
    final etaText = formatEta(task.etaSeconds);
    final statusText = task.cancelRequested ? '取消请求已提交' : task.status;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(children: [
              const Icon(Icons.cloud_download_outlined),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  '${task.repoId.isEmpty ? 'download' : task.repoId} - $statusText',
                  style: const TextStyle(fontWeight: FontWeight.w700),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              if (task.revision != null && task.revision!.isNotEmpty)
                Text(task.revision!, style: const TextStyle(color: Colors.black54)),
            ]),
            const SizedBox(height: 10),
            LinearProgressIndicator(value: task.isRunning ? progressValue : (hasPercent ? progressValue : null)),
            const SizedBox(height: 8),
            Wrap(
              spacing: 16,
              runSpacing: 6,
              children: [
                Text(hasPercent ? '${task.percent!.toStringAsFixed(1)}%' : '进度未知'),
                Text('${formatBytes(task.downloadedBytes)} / $totalText'),
                Text(formatSpeed(task.speedBytesPerSecond)),
                Text(etaText),
                if (task.totalFiles != null)
                  Text('${task.completedFiles ?? 0} / ${task.totalFiles} files'),
                if (task.resumeSupported) const Text('retry 可复用缓存'),
              ],
            ),
            if (task.currentFile != null && task.currentFile!.isNotEmpty) ...[
              const SizedBox(height: 6),
              Text('当前文件: ${task.currentFile}', maxLines: 1, overflow: TextOverflow.ellipsis),
            ],
            if (task.message != null && task.message!.isNotEmpty) ...[
              const SizedBox(height: 6),
              Text(task.message!),
            ],
            if (task.errorMessage != null && task.errorMessage!.isNotEmpty) ...[
              const SizedBox(height: 6),
              Text(
                '${task.errorCode ?? 'DOWNLOAD_FAILED'}: ${task.errorMessage}',
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              ),
            ],
            const SizedBox(height: 10),
            Wrap(spacing: 8, children: [
              TextButton(
                onPressed: task.jobId.isEmpty || !task.canCancel ? null : () => onCancel(task.jobId),
                child: const Text('Cancel'),
              ),
              TextButton(
                onPressed: task.jobId.isEmpty || !task.canRetry ? null : () => onRetry(task.jobId),
                child: const Text('Retry'),
              ),
              if (task.isSucceeded && task.modelId != null && task.modelId!.isNotEmpty)
                FilledButton.tonal(
                  onPressed: () => onViewModel(task.modelId!),
                  child: const Text('查看模型'),
                ),
            ]),
          ],
        ),
      ),
    );
  }
}

