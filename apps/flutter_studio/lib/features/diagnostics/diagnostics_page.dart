import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../core/ui/app_empty_state.dart';
import '../../core/ui/app_section_header.dart';
import '../../core/ui/app_status_badge.dart';

class DiagnosticsPage extends StatelessWidget {
  const DiagnosticsPage({
    super.key,
    required this.runtime,
    required this.capabilities,
    required this.exportResult,
    required this.onExport,
    this.health,
    this.system,
    this.preview,
    this.loading = false,
    this.error,
    this.onRefresh,
  });

  final Map<String, dynamic>? runtime;
  final List<dynamic> capabilities;
  final String? exportResult;
  final VoidCallback onExport;
  final Map<String, dynamic>? health;
  final Map<String, dynamic>? system;
  final Map<String, dynamic>? preview;
  final bool loading;
  final String? error;
  final VoidCallback? onRefresh;

  @override
  Widget build(BuildContext context) {
    final visibleCapabilities = capabilities.isNotEmpty
        ? capabilities
        : ((preview?['capabilities'] as List?) ?? const []);
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppSectionHeader(
            title: '诊断',
            subtitle:
                '导出脱敏诊断包；不包含模型权重、训练检查点、API Key、Cookie、Authorization 请求头或 RAG/小说正文。诊断包不会包含模型权重或敏感凭证。',
            actions: [
              const AppStatusBadge(label: '已脱敏', tone: AppStatusTone.success),
              const SizedBox(width: 8),
              OutlinedButton.icon(
                onPressed: loading ? null : onRefresh,
                icon: const Icon(Icons.refresh),
                label: const Text('刷新检查'),
              ),
              const SizedBox(width: 8),
              FilledButton.icon(
                onPressed: loading ? null : onExport,
                icon: const Icon(Icons.archive_outlined),
                label: const Text('导出诊断'),
              ),
            ],
          ),
          if (loading) const LinearProgressIndicator(),
          if (error != null) ...[
            const SizedBox(height: 12),
            Card(
              color: Theme.of(context).colorScheme.errorContainer,
              child: ListTile(
                leading: const Icon(Icons.error_outline),
                title: const Text('诊断失败'),
                subtitle: SelectableText(error!),
              ),
            ),
          ],
          if (exportResult != null) ...[
            const SizedBox(height: 12),
            Card(
              child: ListTile(
                leading: const Icon(Icons.folder_zip_outlined),
                title: const Text('诊断包已导出'),
                subtitle: SelectableText(exportResult!),
                trailing: IconButton(
                  onPressed: () =>
                      Clipboard.setData(ClipboardData(text: exportResult!)),
                  icon: const Icon(Icons.copy),
                  tooltip: '复制导出结果',
                ),
              ),
            ),
          ],
          const SizedBox(height: 12),
          Expanded(
            child: Row(
              children: [
                Expanded(
                  child: _DiagnosticsCard(
                    title: '健康与系统',
                    child: SelectableText(
                      '运行时\n${runtime ?? {}}\n\n健康状态\n${health ?? {}}\n\n系统\n${system ?? {}}\n\n预览\n${preview ?? {}}',
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _DiagnosticsCard(
                    title: '能力',
                    child: visibleCapabilities.isEmpty
                        ? const AppEmptyState(
                            title: '暂无能力快照',
                            message: '点击“刷新检查”加载诊断能力。',
                            icon: Icons.rule_outlined,
                          )
                        : ListView.separated(
                            itemCount: visibleCapabilities.length,
                            separatorBuilder: (_, _) =>
                                const Divider(height: 1),
                            itemBuilder: (context, index) =>
                                Text('${visibleCapabilities[index]}'),
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

class _DiagnosticsCard extends StatelessWidget {
  const _DiagnosticsCard({required this.title, required this.child});

  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            Expanded(child: child),
          ],
        ),
      ),
    );
  }
}
