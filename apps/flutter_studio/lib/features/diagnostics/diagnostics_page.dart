import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../core/ui/app_section_header.dart';
import '../../core/ui/app_status_badge.dart';

class DiagnosticsPage extends StatelessWidget {
  const DiagnosticsPage({
    super.key,
    required this.runtime,
    required this.capabilities,
    required this.exportResult,
    required this.onExport,
  });

  final Map<String, dynamic>? runtime;
  final List<dynamic> capabilities;
  final String? exportResult;
  final VoidCallback onExport;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        AppSectionHeader(
          title: 'Diagnostics',
          subtitle: '诊断包会脱敏；不会包含模型权重、聊天正文、RAG 文档正文、密码、API Key、Cookie 或 Authorization header。',
          actions: [
            const AppStatusBadge(label: 'Redacted', tone: AppStatusTone.success),
            const SizedBox(width: 8),
            FilledButton.icon(onPressed: onExport, icon: const Icon(Icons.archive_outlined), label: const Text('生成诊断包')),
          ],
        ),
        if (exportResult != null) ...[
          const SizedBox(height: 12),
          Card(
            child: ListTile(
              leading: const Icon(Icons.folder_zip_outlined),
              title: const Text('诊断包已导出'),
              subtitle: SelectableText(exportResult!),
              trailing: IconButton(
                onPressed: () => Clipboard.setData(ClipboardData(text: exportResult!)),
                icon: const Icon(Icons.copy),
                tooltip: '复制路径',
              ),
            ),
          ),
        ],
        const SizedBox(height: 12),
        Expanded(
          child: Row(children: [
            Expanded(
              child: Card(
                child: SingleChildScrollView(
                  padding: const EdgeInsets.all(12),
                  child: SelectableText('Runtime\n${runtime ?? {}}'),
                ),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Card(
                child: ListView.separated(
                  padding: const EdgeInsets.all(12),
                  itemCount: capabilities.length,
                  separatorBuilder: (_, _) => const Divider(height: 1),
                  itemBuilder: (context, index) => Text('${capabilities[index]}'),
                ),
              ),
            ),
          ]),
        ),
      ]),
    );
  }
}
