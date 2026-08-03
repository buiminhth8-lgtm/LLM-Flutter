import 'package:flutter/material.dart';

import '../../core/ui/app_empty_state.dart';
import '../../core/ui/app_section_header.dart';
import '../../core/ui/app_status_badge.dart';

class StoragePage extends StatelessWidget {
  const StoragePage({
    super.key,
    required this.storage,
    required this.cleanupPreview,
    required this.onRefresh,
    required this.onPreview,
    required this.onCleanup,
  });

  final Map<String, dynamic>? storage;
  final Map<String, dynamic>? cleanupPreview;
  final VoidCallback onRefresh;
  final VoidCallback onPreview;
  final VoidCallback onCleanup;

  @override
  Widget build(BuildContext context) {
    final categories = storage?['categories'] is List
        ? storage!['categories'] as List
        : const [];
    final items = cleanupPreview?['items'] is List
        ? cleanupPreview!['items'] as List
        : const [];
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppSectionHeader(
            title: '存储',
            subtitle: '清理前必须先 Preview；正式模型、外部模型和 RAG 原始文档默认受保护。',
            actions: [
              IconButton.filledTonal(
                onPressed: onRefresh,
                icon: const Icon(Icons.refresh),
                tooltip: '刷新',
              ),
              const SizedBox(width: 8),
              OutlinedButton.icon(
                onPressed: onPreview,
                icon: const Icon(Icons.fact_check),
                label: const Text('预览清理'),
              ),
              const SizedBox(width: 8),
              FilledButton.icon(
                onPressed: items.isEmpty ? null : onCleanup,
                icon: const Icon(Icons.cleaning_services),
                label: const Text('执行清理'),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Expanded(
            child: Row(
              children: [
                Expanded(
                  child: Card(
                    child: categories.isEmpty
                        ? const AppEmptyState(
                            title: '暂无存储统计',
                            message: '点击刷新获取磁盘分类占用。',
                          )
                        : ListView.separated(
                            padding: const EdgeInsets.all(8),
                            itemCount: categories.length,
                            separatorBuilder: (_, _) =>
                                const Divider(height: 1),
                            itemBuilder: (context, index) {
                              final map = categories[index] is Map
                                  ? categories[index] as Map
                                  : const {};
                              final cleanable = map['cleanable'] == true;
                              return ListTile(
                                leading: Icon(
                                  cleanable
                                      ? Icons.delete_sweep_outlined
                                      : Icons.lock_outline,
                                ),
                                title: Row(
                                  children: [
                                    Expanded(
                                      child: Text(
                                        '${map['name'] ?? 'category'}',
                                      ),
                                    ),
                                    AppStatusBadge(
                                      label: cleanable ? '可清理' : '受保护',
                                      tone: cleanable
                                          ? AppStatusTone.info
                                          : AppStatusTone.neutral,
                                    ),
                                  ],
                                ),
                                subtitle: Text(
                                  '${map['size_bytes'] ?? 0} bytes',
                                ),
                              );
                            },
                          ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Card(
                    child: items.isEmpty
                        ? const AppEmptyState(
                            title: '未生成清理预览',
                            message:
                                '先执行 Preview cleanup，确认待清理目录后才能执行 cleanup。',
                            icon: Icons.fact_check_outlined,
                          )
                        : ListView.separated(
                            padding: const EdgeInsets.all(8),
                            itemCount: items.length,
                            separatorBuilder: (_, _) =>
                                const Divider(height: 1),
                            itemBuilder: (context, index) {
                              final map = items[index] is Map
                                  ? items[index] as Map
                                  : const {};
                              return ListTile(
                                leading: const Icon(Icons.preview_outlined),
                                title: Text(
                                  '${map['category'] ?? 'cleanup item'}',
                                ),
                                subtitle: Text(
                                  '${map['path'] ?? ''}\n${map['reason'] ?? ''} · ${map['size_bytes'] ?? 0} bytes',
                                ),
                              );
                            },
                          ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
