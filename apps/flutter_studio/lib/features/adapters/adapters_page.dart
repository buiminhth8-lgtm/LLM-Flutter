import 'package:flutter/material.dart';

import '../../core/ui/app_empty_state.dart';
import '../../core/ui/app_section_header.dart';
import '../../core/ui/app_status_badge.dart';

class AdaptersPage extends StatelessWidget {
  const AdaptersPage({
    super.key,
    required this.adapters,
    required this.currentModel,
    required this.hasModelContext,
    required this.onRefresh,
    required this.onScan,
    required this.onLoad,
    required this.onActivate,
    required this.onDeactivate,
  });

  final List<dynamic> adapters;
  final Map<String, dynamic>? currentModel;
  final bool hasModelContext;
  final VoidCallback onRefresh;
  final VoidCallback onScan;
  final Future<void> Function(String id) onLoad;
  final Future<void> Function(String id) onActivate;
  final Future<void> Function(String id) onDeactivate;

  @override
  Widget build(BuildContext context) {
    final active = '${currentModel?['adapter_id'] ?? currentModel?['adapter'] ?? ''}';
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        AppSectionHeader(
          title: 'Adapters',
          subtitle: hasModelContext ? '当前基础模型可用于加载和激活 Adapter。' : '请先加载或选择基础模型，再加载或激活 Adapter。',
          actions: [
            OutlinedButton.icon(onPressed: onScan, icon: const Icon(Icons.manage_search), label: const Text('扫描')),
            const SizedBox(width: 8),
            FilledButton.icon(onPressed: onRefresh, icon: const Icon(Icons.refresh), label: const Text('刷新')),
          ],
        ),
        const SizedBox(height: 12),
        Expanded(
          child: adapters.isEmpty
              ? const AppEmptyState(
                  title: '没有发现 Adapter',
                  message: '请扫描 Adapter 目录，或通过后端注册 Adapter。',
                  icon: Icons.extension_outlined,
                )
              : ListView.separated(
                  itemCount: adapters.length,
                  separatorBuilder: (_, _) => const SizedBox(height: 8),
                  itemBuilder: (context, index) {
                    final map = adapters[index] is Map ? adapters[index] as Map : const {};
                    final id = '${map['id'] ?? ''}';
                    final compatible = map['compatible'] != false;
                    final isActive = active.isNotEmpty && active == id;
                    return Card(
                      child: ListTile(
                        leading: Icon(isActive ? Icons.extension : Icons.extension_outlined),
                        title: Row(
                          children: [
                            Expanded(child: Text('${map['name'] ?? map['id'] ?? 'adapter'}')),
                            if (isActive) const AppStatusBadge(label: 'Active', tone: AppStatusTone.success),
                            if (!compatible) const AppStatusBadge(label: '不兼容', tone: AppStatusTone.warning),
                          ],
                        ),
                        subtitle: Text(
                          [
                            'base: ${map['base_model_name_or_path'] ?? 'unknown'}',
                            'peft: ${map['peft_type'] ?? 'unknown'}  rank: ${map['rank'] ?? 'unknown'}  alpha: ${map['alpha'] ?? 'unknown'}',
                            'target: ${map['target_modules'] ?? 'unknown'}',
                          ].join('\n'),
                        ),
                        isThreeLine: true,
                        trailing: Wrap(spacing: 8, children: [
                          FilledButton.tonal(
                            onPressed: compatible && hasModelContext && id.isNotEmpty ? () => onLoad(id) : null,
                            child: const Text('Load'),
                          ),
                          FilledButton(
                            onPressed: compatible && hasModelContext && id.isNotEmpty && !isActive ? () => onActivate(id) : null,
                            child: Text(isActive ? 'Active' : 'Activate'),
                          ),
                          TextButton(
                            onPressed: isActive && hasModelContext ? () => onDeactivate(id) : null,
                            child: const Text('Deactivate'),
                          ),
                        ]),
                      ),
                    );
                  },
                ),
        ),
      ]),
    );
  }
}
