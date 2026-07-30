import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../core/models/dto.dart';
import '../../core/ui/app_confirm_dialog.dart';
import '../../core/ui/app_empty_state.dart';
import '../../core/ui/app_progress_bar.dart';
import '../../core/ui/app_section_header.dart';
import '../../core/ui/app_status_badge.dart';
import '../../core/utils/formatters.dart';

class DownloadsPage extends StatelessWidget {
  const DownloadsPage({
    super.key,
    required this.downloads,
    required this.repoController,
    required this.provider,
    required this.revisionController,
    required this.allowPatternsController,
    required this.ignorePatternsController,
    required this.onStart,
    required this.onProviderChanged,
    required this.onCancel,
    required this.onRetry,
    required this.onDelete,
    required this.onViewModel,
    required this.onRefresh,
  });

  final List<DownloadTaskDto> downloads;
  final TextEditingController repoController;
  final String provider;
  final TextEditingController revisionController;
  final TextEditingController allowPatternsController;
  final TextEditingController ignorePatternsController;
  final VoidCallback onStart;
  final ValueChanged<String> onProviderChanged;
  final Future<void> Function(String id) onCancel;
  final Future<void> Function(String id) onRetry;
  final Future<void> Function(String id) onDelete;
  final Future<void> Function(String modelId) onViewModel;
  final VoidCallback onRefresh;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppSectionHeader(
            title: 'Downloads',
            subtitle: '下载通过后台 Job 运行；总大小未知时不显示伪造百分比，取消是协作式请求。',
            actions: [
              IconButton.filledTonal(
                onPressed: onRefresh,
                icon: const Icon(Icons.refresh),
                tooltip: '刷新',
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              SizedBox(
                width: 220,
                child: InputDecorator(
                  decoration: const InputDecoration(
                    labelText: 'Provider',
                    border: OutlineInputBorder(),
                  ),
                  child: Text(
                    _providerLabel(provider),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: TextField(
                  controller: repoController,
                  decoration: const InputDecoration(
                    labelText: 'ModelScope model_id',
                    border: OutlineInputBorder(),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              SizedBox(
                width: 180,
                child: TextField(
                  controller: revisionController,
                  decoration: const InputDecoration(
                    labelText: 'Revision',
                    border: OutlineInputBorder(),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              FilledButton.icon(
                onPressed: onStart,
                icon: const Icon(Icons.download),
                label: const Text('开始下载'),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: allowPatternsController,
                  decoration: const InputDecoration(
                    labelText: 'Allow patterns，用逗号分隔',
                    border: OutlineInputBorder(),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: TextField(
                  controller: ignorePatternsController,
                  decoration: const InputDecoration(
                    labelText: 'Ignore patterns，用逗号分隔',
                    border: OutlineInputBorder(),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Expanded(
            child: downloads.isEmpty
                ? const AppEmptyState(
                    title: '没有下载任务',
                    message: '输入 ModelScope model_id 后创建后台下载任务。',
                    icon: Icons.cloud_download_outlined,
                  )
                : ListView.separated(
                    itemCount: downloads.length,
                    separatorBuilder: (_, _) => const SizedBox(height: 8),
                    itemBuilder: (context, index) => _DownloadCard(
                      task: downloads[index],
                      onCancel: onCancel,
                      onRetry: onRetry,
                      onDelete: onDelete,
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
    required this.onDelete,
    required this.onViewModel,
  });

  final DownloadTaskDto task;
  final Future<void> Function(String id) onCancel;
  final Future<void> Function(String id) onRetry;
  final Future<void> Function(String id) onDelete;
  final Future<void> Function(String modelId) onViewModel;

  @override
  Widget build(BuildContext context) {
    final hasPercent = task.percent != null;
    final progressValue = hasPercent
        ? (task.percent! / 100).clamp(0.0, 1.0)
        : null;
    final displayedProgressValue = task.isRunning
        ? progressValue
        : (hasPercent ? progressValue : 0.0);
    final progressLabel = hasPercent
        ? '${task.percent!.toStringAsFixed(1)}%'
        : _progressLabel(task);
    final totalText = task.totalBytes == null
        ? '总大小未知'
        : formatBytes(task.totalBytes);
    final statusText = task.cancelRequested ? '取消请求已提交' : task.status;
    final providerLabel = _providerLabel(task.provider);
    final errorText =
        '${task.errorCode ?? 'DOWNLOAD_FAILED'}: ${task.errorMessage}';
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.cloud_download_outlined),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    task.repoId.isEmpty
                        ? providerLabel
                        : '$providerLabel: ${task.repoId}',
                    style: const TextStyle(fontWeight: FontWeight.w700),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                AppStatusBadge(
                  label: statusText,
                  tone: _statusTone(task.status),
                ),
                if (task.revision != null && task.revision!.isNotEmpty) ...[
                  const SizedBox(width: 8),
                  Text(
                    task.revision!,
                    style: TextStyle(
                      color: Theme.of(context).colorScheme.onSurfaceVariant,
                    ),
                  ),
                ],
              ],
            ),
            const SizedBox(height: 10),
            AppProgressBar(value: displayedProgressValue, label: progressLabel),
            const SizedBox(height: 8),
            Wrap(
              spacing: 16,
              runSpacing: 6,
              children: [
                Text('${formatBytes(task.downloadedBytes)} / $totalText'),
                Text(formatSpeed(task.speedBytesPerSecond)),
                Text(formatEta(task.etaSeconds)),
                if (task.totalFiles != null)
                  Text(
                    '${task.completedFiles ?? 0} / ${task.totalFiles} files',
                  ),
                if (task.resumeSupported) Text('重试会复用 $providerLabel cache'),
              ],
            ),
            if (task.currentFile != null && task.currentFile!.isNotEmpty) ...[
              const SizedBox(height: 6),
              Text(
                '当前文件：${task.currentFile}',
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ],
            if (task.message != null && task.message!.isNotEmpty) ...[
              const SizedBox(height: 6),
              Text(task.message!),
            ],
            if (task.errorMessage != null && task.errorMessage!.isNotEmpty) ...[
              const SizedBox(height: 6),
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: SelectableText(
                      errorText,
                      style: TextStyle(
                        color: Theme.of(context).colorScheme.error,
                      ),
                    ),
                  ),
                  IconButton(
                    tooltip: '复制错误信息',
                    onPressed: () =>
                        Clipboard.setData(ClipboardData(text: errorText)),
                    icon: const Icon(Icons.copy),
                  ),
                ],
              ),
            ],
            const SizedBox(height: 10),
            Wrap(
              spacing: 8,
              children: [
                TextButton(
                  onPressed: task.jobId.isEmpty || !task.canCancel
                      ? null
                      : () => onCancel(task.jobId),
                  child: const Text('取消'),
                ),
                TextButton(
                  onPressed: task.jobId.isEmpty || !task.canRetry
                      ? null
                      : () => onRetry(task.jobId),
                  child: const Text('重试'),
                ),
                TextButton.icon(
                  onPressed: task.jobId.isEmpty || !task.canDelete
                      ? null
                      : () async {
                          final confirmed = await showAppConfirmDialog(
                            context,
                            title: '删除下载记录？',
                            message: '只会删除这条下载历史记录，不会删除模型文件、下载缓存或临时目录。',
                            confirmLabel: '删除记录',
                            destructive: true,
                          );
                          if (confirmed) {
                            await onDelete(task.jobId);
                          }
                        },
                  icon: const Icon(Icons.delete_outline),
                  label: const Text('删除记录'),
                ),
                if (task.isSucceeded &&
                    task.modelId != null &&
                    task.modelId!.isNotEmpty)
                  FilledButton.tonal(
                    onPressed: () => onViewModel(task.modelId!),
                    child: const Text('查看模型'),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  AppStatusTone _statusTone(String status) {
    return switch (status) {
      'succeeded' => AppStatusTone.success,
      'failed' => AppStatusTone.danger,
      'cancelled' => AppStatusTone.warning,
      'running' || 'pending' || 'cancelling' => AppStatusTone.info,
      _ => AppStatusTone.neutral,
    };
  }

  String _progressLabel(DownloadTaskDto task) {
    if (task.isFailed) {
      return '下载失败';
    }
    if (task.isCancelled) {
      return '已取消';
    }
    if (task.isInterrupted) {
      return '已中断';
    }
    if (task.isSucceeded) {
      return '已完成';
    }
    return '进度未知';
  }
}

String _providerLabel(String provider) => 'ModelScope / 魔塔社区';
