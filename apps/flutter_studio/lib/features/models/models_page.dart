import 'package:flutter/material.dart';

import '../../core/ui/app_confirm_dialog.dart';
import '../../core/ui/app_empty_state.dart';
import '../../core/ui/app_section_header.dart';
import '../../core/ui/app_status_badge.dart';

class ModelsPage extends StatefulWidget {
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
  State<ModelsPage> createState() => _ModelsPageState();
}

class _ModelsPageState extends State<ModelsPage> {
  final _searchController = TextEditingController();
  String _statusFilter = 'all';
  int _selectedIndex = 0;

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final models = _filteredModels();
    final selected = models.isEmpty
        ? null
        : _asMap(models[_selectedIndex.clamp(0, models.length - 1)]);
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppSectionHeader(
            title: '模型',
            subtitle: '扫描、加载、选择聊天模型，或将受管理模型移入回收站。',
            actions: [
              OutlinedButton.icon(
                onPressed: widget.onRegisterExternal,
                icon: const Icon(Icons.add_link),
                label: const Text('注册外部模型'),
              ),
              const SizedBox(width: 8),
              OutlinedButton.icon(
                onPressed: widget.onScan,
                icon: const Icon(Icons.manage_search),
                label: const Text('扫描'),
              ),
              const SizedBox(width: 8),
              FilledButton.icon(
                onPressed: widget.onRefresh,
                icon: const Icon(Icons.refresh),
                label: const Text('刷新'),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Expanded(
            child: widget.models.isEmpty
                ? AppEmptyState(
                    title: '没有发现模型',
                    message: '请先扫描模型目录、注册外部模型，或在下载页面下载模型。',
                    icon: Icons.view_in_ar_outlined,
                    action: FilledButton.icon(
                      onPressed: widget.onScan,
                      icon: const Icon(Icons.manage_search),
                      label: const Text('扫描模型'),
                    ),
                  )
                : Row(
                    children: [
                      SizedBox(
                        width: 360,
                        child: Column(
                          children: [
                            TextField(
                              controller: _searchController,
                              decoration: const InputDecoration(
                                labelText: '搜索模型',
                                prefixIcon: Icon(Icons.search),
                                border: OutlineInputBorder(),
                              ),
                              onChanged: (_) =>
                                  setState(() => _selectedIndex = 0),
                            ),
                            const SizedBox(height: 8),
                            SegmentedButton<String>(
                              segments: const [
                                ButtonSegment(value: 'all', label: Text('全部')),
                                ButtonSegment(
                                  value: 'ready',
                                  label: Text('就绪'),
                                ),
                                ButtonSegment(
                                  value: 'incomplete',
                                  label: Text('不完整'),
                                ),
                                ButtonSegment(
                                  value: 'unsupported',
                                  label: Text('不支持'),
                                ),
                              ],
                              selected: {_statusFilter},
                              onSelectionChanged: (value) => setState(() {
                                _statusFilter = value.first;
                                _selectedIndex = 0;
                              }),
                            ),
                            const SizedBox(height: 8),
                            Expanded(
                              child: ListView.separated(
                                itemCount: models.length,
                                separatorBuilder: (_, _) =>
                                    const SizedBox(height: 8),
                                itemBuilder: (context, index) {
                                  final map = _asMap(models[index]);
                                  final id = '${map['id'] ?? ''}';
                                  final status =
                                      '${map['status'] ?? 'unknown'}';
                                  final isLoaded =
                                      widget.currentModel?['loaded'] == true &&
                                      widget.currentModel?['model_id'] == id;
                                  return Card(
                                    color: index == _selectedIndex
                                        ? Theme.of(
                                            context,
                                          ).colorScheme.primaryContainer
                                        : null,
                                    child: ListTile(
                                      selected: index == _selectedIndex,
                                      leading: Icon(
                                        isLoaded
                                            ? Icons.check_circle
                                            : Icons.view_in_ar_outlined,
                                      ),
                                      title: Text(
                                        '${map['display_name'] ?? map['id'] ?? 'unknown'}',
                                        maxLines: 1,
                                        overflow: TextOverflow.ellipsis,
                                      ),
                                      subtitle: Text(
                                        '$status · ${map['format'] ?? 'unknown'}',
                                      ),
                                      onTap: () => setState(
                                        () => _selectedIndex = index,
                                      ),
                                    ),
                                  );
                                },
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: selected == null
                            ? const AppEmptyState(title: '请选择模型')
                            : _ModelDetails(
                                model: selected,
                                currentModel: widget.currentModel,
                                selectedModelId: widget.selectedModelId,
                                onLoad: widget.onLoad,
                                onUnload: widget.onUnload,
                                onSelect: widget.onSelect,
                                onMoveToTrash: widget.onMoveToTrash,
                              ),
                      ),
                    ],
                  ),
          ),
        ],
      ),
    );
  }

  List<dynamic> _filteredModels() {
    final query = _searchController.text.trim().toLowerCase();
    return widget.models.where((item) {
      final map = _asMap(item);
      final status = '${map['status'] ?? 'unknown'}'.toLowerCase();
      final haystack =
          '${map['display_name'] ?? ''} ${map['id'] ?? ''} ${map['path'] ?? ''}'
              .toLowerCase();
      final matchesQuery = query.isEmpty || haystack.contains(query);
      final matchesStatus = _statusFilter == 'all' || status == _statusFilter;
      return matchesQuery && matchesStatus;
    }).toList();
  }

  Map _asMap(dynamic item) => item is Map ? item : const {};
}

class _ModelDetails extends StatelessWidget {
  const _ModelDetails({
    required this.model,
    required this.currentModel,
    required this.selectedModelId,
    required this.onLoad,
    required this.onUnload,
    required this.onSelect,
    required this.onMoveToTrash,
  });

  final Map model;
  final Map<String, dynamic>? currentModel;
  final String? selectedModelId;
  final Future<void> Function(String modelId) onLoad;
  final VoidCallback onUnload;
  final Future<void> Function(String modelId) onSelect;
  final Future<void> Function(String modelId) onMoveToTrash;

  @override
  Widget build(BuildContext context) {
    final id = '${model['id'] ?? ''}';
    final status = '${model['status'] ?? 'unknown'}';
    final isReady = status == 'ready';
    final isLoaded =
        currentModel?['loaded'] == true && currentModel?['model_id'] == id;
    final isSelected = selectedModelId == id;
    final compatibility = model['compatibility'] is Map
        ? model['compatibility'] as Map
        : const {};
    final statusTone = switch (status) {
      'ready' => AppStatusTone.success,
      'unsupported' => AppStatusTone.warning,
      'corrupted' => AppStatusTone.danger,
      'incomplete' => AppStatusTone.warning,
      _ => AppStatusTone.neutral,
    };
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(
                      '${model['display_name'] ?? model['id'] ?? model['path'] ?? 'unknown'}',
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
                  AppStatusBadge(label: status, tone: statusTone),
                  if (isLoaded) ...[
                    const SizedBox(width: 8),
                    const AppStatusBadge(
                      label: '已加载',
                      tone: AppStatusTone.success,
                    ),
                  ],
                  if (isSelected) ...[
                    const SizedBox(width: 8),
                    const AppStatusBadge(
                      label: '聊天模型',
                      tone: AppStatusTone.info,
                    ),
                  ],
                ],
              ),
              const SizedBox(height: 16),
              Wrap(
                spacing: 24,
                runSpacing: 12,
                children: [
                  _Meta(label: '格式', value: '${model['format'] ?? 'unknown'}'),
                  _Meta(
                    label: '架构',
                    value: '${model['architecture'] ?? 'unknown'}',
                  ),
                  _Meta(
                    label: '参数量',
                    value: '${model['parameter_count'] ?? 'unknown'}',
                  ),
                  _Meta(
                    label: '量化',
                    value: '${model['quantization'] ?? 'none'}',
                  ),
                  _Meta(
                    label: '兼容风险',
                    value:
                        '${compatibility['risk_level'] ?? model['risk_level'] ?? 'unknown'}',
                  ),
                  _Meta(
                    label: '推荐后端',
                    value: '${compatibility['recommended_backend'] ?? 'auto'}',
                  ),
                  _Meta(
                    label: '来源 repo',
                    value: '${model['repo_id'] ?? 'unknown'}',
                  ),
                  _Meta(
                    label: 'revision',
                    value: '${model['revision'] ?? 'unknown'}',
                  ),
                ],
              ),
              const SizedBox(height: 16),
              SelectableText('${model['path'] ?? ''}'),
              const SizedBox(height: 20),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  FilledButton.tonal(
                    onPressed: id.isEmpty ? null : () => onSelect(id),
                    child: const Text('设为聊天模型'),
                  ),
                  FilledButton.icon(
                    onPressed: isReady && !isLoaded && id.isNotEmpty
                        ? () => onLoad(id)
                        : null,
                    icon: const Icon(Icons.play_arrow),
                    label: Text(isLoaded ? '已加载' : '加载'),
                  ),
                  OutlinedButton.icon(
                    onPressed: isLoaded ? onUnload : null,
                    icon: const Icon(Icons.eject),
                    label: const Text('卸载'),
                  ),
                  OutlinedButton.icon(
                    onPressed: null,
                    icon: const Icon(Icons.folder_open),
                    label: const Text('打开目录'),
                  ),
                  FilledButton.icon(
                    style: FilledButton.styleFrom(
                      backgroundColor: Theme.of(context).colorScheme.error,
                      foregroundColor: Theme.of(context).colorScheme.onError,
                    ),
                    onPressed: id.isEmpty
                        ? null
                        : () async {
                            final confirmed = await showAppConfirmDialog(
                              context,
                              title: '移入回收站？',
                              message: '不会直接永久删除模型。受管理模型会移入回收站，外部模型默认只取消注册。',
                              confirmLabel: '移入回收站',
                              destructive: true,
                            );
                            if (confirmed) {
                              await onMoveToTrash(id);
                            }
                          },
                    icon: const Icon(Icons.delete_outline),
                    label: const Text('移入回收站'),
                  ),
                ],
              ),
              if (!isReady) ...[
                const SizedBox(height: 10),
                Text(
                  '该模型当前状态为 $status，不能加载。请重新扫描或检查模型文件完整性。',
                  style: TextStyle(color: Theme.of(context).colorScheme.error),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _Meta extends StatelessWidget {
  const _Meta({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 180,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: TextStyle(
              color: Theme.of(context).colorScheme.onSurfaceVariant,
            ),
          ),
          const SizedBox(height: 2),
          Text(value, maxLines: 2, overflow: TextOverflow.ellipsis),
        ],
      ),
    );
  }
}
