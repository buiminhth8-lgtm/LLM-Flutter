import 'package:flutter/material.dart';

class ModelsPage extends StatelessWidget {
  const ModelsPage({
    super.key,
    required this.models,
    required this.currentModel,
    required this.selectedModelId,
    required this.onRefresh,
    required this.onScan,
    required this.onLoad,
    required this.onUnload,
    required this.onSelect,
    required this.onRegisterExternal,
    required this.onMoveToTrash,
  });

  final List<dynamic> models;
  final Map<String, dynamic>? currentModel;
  final String? selectedModelId;
  final VoidCallback onRefresh;
  final VoidCallback onScan;
  final Future<void> Function(String modelId) onLoad;
  final VoidCallback onUnload;
  final Future<void> Function(String modelId) onSelect;
  final VoidCallback onRegisterExternal;
  final Future<void> Function(String modelId) onMoveToTrash;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Text('Local models', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
              const Spacer(),
              OutlinedButton.icon(onPressed: onRegisterExternal, icon: const Icon(Icons.add_link), label: const Text('Register external')),
              const SizedBox(width: 8),
              OutlinedButton.icon(onPressed: onScan, icon: const Icon(Icons.manage_search), label: const Text('Scan')),
              const SizedBox(width: 8),
              FilledButton.icon(onPressed: onRefresh, icon: const Icon(Icons.search), label: const Text('Refresh')),
            ],
          ),
          const SizedBox(height: 12),
          Expanded(
            child: models.isEmpty
                ? const Center(child: Text('No models found. Register or download a model first.'))
                : ListView.separated(
                    itemCount: models.length,
                    separatorBuilder: (_, _) => const SizedBox(height: 8),
                    itemBuilder: (context, index) {
                      final map = models[index] is Map ? models[index] as Map : const {};
                      final id = '${map['id'] ?? ''}';
                      final status = '${map['status'] ?? 'unknown'}';
                      final isReady = status == 'ready';
                      final isLoaded = currentModel?['loaded'] == true && currentModel?['model_id'] == id;
                      final isSelected = selectedModelId == id;
                      final compatibility = map['compatibility'] is Map ? map['compatibility'] as Map : const {};
                      return Card(
                        child: ListTile(
                          leading: Icon(isLoaded ? Icons.check_circle : Icons.view_in_ar),
                          title: Text('${map['display_name'] ?? map['id'] ?? map['path'] ?? 'unknown'}'),
                          subtitle: Text([
                            '${map['format'] ?? 'unknown'} - $status',
                            'arch: ${map['architecture'] ?? 'unknown'}  params: ${map['parameter_count'] ?? 'unknown'}  quant: ${map['quantization'] ?? 'none'}',
                            'risk: ${compatibility['risk_level'] ?? map['risk_level'] ?? 'unknown'}  backend: ${compatibility['recommended_backend'] ?? 'auto'}',
                            '${map['path'] ?? ''}',
                          ].join('\n')),
                          isThreeLine: true,
                          trailing: Wrap(
                            spacing: 8,
                            children: [
                              if (isSelected) const Chip(label: Text('Chat')),
                              TextButton(onPressed: id.isEmpty ? null : () => onSelect(id), child: const Text('Use')),
                              FilledButton.tonal(onPressed: isReady && !isLoaded ? () => onLoad(id) : null, child: Text(isLoaded ? 'Loaded' : 'Load')),
                              if (isLoaded) IconButton(onPressed: onUnload, icon: const Icon(Icons.eject), tooltip: 'Unload'),
                              IconButton(
                                onPressed: id.isEmpty ? null : () async {
                                  final confirmed = await showDialog<bool>(
                                    context: context,
                                    builder: (context) => AlertDialog(
                                      title: const Text('Move model to trash?'),
                                      content: const Text('Managed models are moved to trash. External models are unregistered by default.'),
                                      actions: [
                                        TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancel')),
                                        FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Move')),
                                      ],
                                    ),
                                  );
                                  if (confirmed == true) {
                                    await onMoveToTrash(id);
                                  }
                                },
                                icon: const Icon(Icons.delete_outline),
                                tooltip: 'Move to trash',
                              ),
                            ],
                          ),
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
