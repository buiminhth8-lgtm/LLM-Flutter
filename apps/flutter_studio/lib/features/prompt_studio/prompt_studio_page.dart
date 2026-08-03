import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../core/ui/app_empty_state.dart';
import '../../core/ui/app_section_header.dart';
import 'models/prompt_template_dto.dart';
import 'prompt_controller.dart';

const promptTypeLabels = {
  'chapter_generate': '章节生成',
  'chapter_continue': '章节续写',
  'chapter_rewrite': '章节重写',
  'chapter_polish': '润色',
  'chapter_expand': '扩写',
  'dialogue_enhance': '对白增强',
  'scene_expand': '场景扩写',
  'outline_generate': '大纲生成',
  'character_generate': '人物生成',
  'world_entry_generate': '世界观生成',
  'summary_generate': '摘要生成',
  'custom': '自定义',
};

const promptCategoryLabels = {
  'writing': '正文生成',
  'planning': '规划设定',
  'editing': '辅助编辑',
};

String promptCategoryLabel(String? category) {
  if (category == null) {
    return '自定义';
  }
  return promptCategoryLabels[category] ?? '自定义';
}

class PromptStudioPage extends StatefulWidget {
  const PromptStudioPage({super.key, required this.controller});

  final PromptController controller;

  @override
  State<PromptStudioPage> createState() => _PromptStudioPageState();
}

class _PromptStudioPageState extends State<PromptStudioPage> {
  final _name = TextEditingController(text: '章节生成模板');
  final _description = TextEditingController();
  final _instruction = TextEditingController(
    text: '小说标题：{{project_title}}\n章节大纲：{{chapter_outline}}\n请输出正文。',
  );
  final _schema = TextEditingController(
    text:
        '{"project_title":{"type":"string","required":true},"chapter_outline":{"type":"string","required":true}}',
  );
  final _defaults = TextEditingController(
    text: '{"target_length":"1200-1800 中文字符"}',
  );
  final _variables = TextEditingController(
    text: '{"project_title":"示例小说","chapter_outline":"主角第一次进入黑市。"}',
  );
  String _type = 'chapter_generate';

  @override
  void dispose() {
    _name.dispose();
    _description.dispose();
    _instruction.dispose();
    _schema.dispose();
    _defaults.dispose();
    _variables.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = widget.controller.state;
    final selected = state.selectedTemplate;
    final validSchema = widget.controller.isValidJsonObject(_schema.text);
    final validDefaults = widget.controller.isValidJsonObject(_defaults.text);
    final validVariables = widget.controller.isValidJsonObject(_variables.text);
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppSectionHeader(
            title: '提示词工作室',
            subtitle: '阶段 2：模板版本、变量校验与渲染预览；不连接模型生成。',
            actions: [
              IconButton.filledTonal(
                onPressed: widget.controller.refresh,
                icon: const Icon(Icons.refresh),
                tooltip: '刷新',
              ),
              FilledButton.icon(
                onPressed: widget.controller.ensureDefaults,
                icon: const Icon(Icons.library_add_outlined),
                label: const Text('确保默认模板'),
              ),
            ],
          ),
          const SizedBox(height: 12),
          if (state.error != null)
            MaterialBanner(
              content: Text(state.error!),
              leading: const Icon(Icons.error_outline),
              actions: [
                TextButton(
                  onPressed: () => setState(() {}),
                  child: const Text('关闭'),
                ),
              ],
            ),
          Expanded(
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                SizedBox(
                  width: 320,
                  child: _TemplateList(
                    templates: state.templates,
                    selected: selected,
                    onSelect: widget.controller.selectTemplate,
                  ),
                ),
                const VerticalDivider(width: 24),
                SizedBox(
                  width: 420,
                  child: ListView(
                    children: [
                      Text(
                        '创建模板',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 8),
                      TextField(
                        controller: _name,
                        decoration: const InputDecoration(
                          labelText: 'name',
                          border: OutlineInputBorder(),
                        ),
                      ),
                      const SizedBox(height: 8),
                      DropdownButtonFormField<String>(
                        initialValue: _type,
                        items: [
                          for (final entry in promptTypeLabels.entries)
                            DropdownMenuItem(
                              value: entry.key,
                              child: Text(entry.value),
                            ),
                        ],
                        onChanged: (value) =>
                            setState(() => _type = value ?? 'custom'),
                        decoration: const InputDecoration(
                          labelText: 'type',
                          border: OutlineInputBorder(),
                        ),
                      ),
                      const SizedBox(height: 8),
                      TextField(
                        controller: _description,
                        decoration: const InputDecoration(
                          labelText: 'description',
                          border: OutlineInputBorder(),
                        ),
                      ),
                      const SizedBox(height: 8),
                      TextField(
                        controller: _instruction,
                        minLines: 5,
                        maxLines: 8,
                        decoration: const InputDecoration(
                          labelText: 'instruction_template',
                          border: OutlineInputBorder(),
                        ),
                      ),
                      const SizedBox(height: 8),
                      TextField(
                        controller: _schema,
                        minLines: 3,
                        maxLines: 5,
                        onChanged: (_) => setState(() {}),
                        decoration: InputDecoration(
                          labelText: '变量结构 JSON',
                          border: const OutlineInputBorder(),
                          errorText: validSchema ? null : '必须是合法 JSON object',
                        ),
                      ),
                      const SizedBox(height: 8),
                      TextField(
                        controller: _defaults,
                        minLines: 2,
                        maxLines: 4,
                        onChanged: (_) => setState(() {}),
                        decoration: InputDecoration(
                          labelText: '默认值 JSON',
                          border: const OutlineInputBorder(),
                          errorText: validDefaults ? null : '必须是合法 JSON object',
                        ),
                      ),
                      const SizedBox(height: 8),
                      FilledButton.icon(
                        onPressed:
                            validSchema &&
                                validDefaults &&
                                _name.text.trim().isNotEmpty &&
                                _instruction.text.trim().isNotEmpty
                            ? () => widget.controller.createTemplate(
                                name: _name.text.trim(),
                                type: _type,
                                description: _description.text.trim(),
                                instructionTemplate: _instruction.text,
                                variablesSchemaJson: _schema.text,
                                defaultValuesJson: _defaults.text,
                              )
                            : null,
                        icon: const Icon(Icons.save_outlined),
                        label: const Text('创建模板'),
                      ),
                    ],
                  ),
                ),
                const VerticalDivider(width: 24),
                Expanded(
                  child: selected == null
                      ? const AppEmptyState(
                          title: '暂无提示词模板',
                          message: '请先创建或确保默认模板存在。',
                          icon: Icons.description_outlined,
                        )
                      : _PreviewPanel(
                          controller: widget.controller,
                          template: selected,
                          variables: _variables,
                          variablesValid: validVariables,
                          onVariablesChanged: () => setState(() {}),
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

class _TemplateList extends StatelessWidget {
  const _TemplateList({
    required this.templates,
    required this.selected,
    required this.onSelect,
  });

  final List<PromptTemplateDto> templates;
  final PromptTemplateDto? selected;
  final ValueChanged<String> onSelect;

  @override
  Widget build(BuildContext context) {
    if (templates.isEmpty) {
      return const AppEmptyState(
        title: '暂无模板',
        message: '请使用“确保默认模板”或创建提示词模板。',
        icon: Icons.description_outlined,
      );
    }
    final grouped = <String, List<PromptTemplateDto>>{};
    for (final template in templates) {
      grouped
          .putIfAbsent(promptCategoryLabel(template.category), () => [])
          .add(template);
    }
    const order = ['正文生成', '规划设定', '辅助编辑', '自定义'];
    final sections = <(String, List<PromptTemplateDto>)>[
      for (final label in order)
        if (grouped.containsKey(label)) (label, grouped[label]!),
      for (final entry in grouped.entries)
        if (!order.contains(entry.key)) (entry.key, entry.value),
    ];
    return ListView(
      children: [
        for (final (label, items) in sections) ...[
          Padding(
            padding: const EdgeInsets.fromLTRB(4, 4, 4, 8),
            child: Text(
              label,
              style: Theme.of(context).textTheme.titleSmall,
            ),
          ),
          for (final template in items) ...[
            _TemplateTile(
              template: template,
              isSelected: template.id == selected?.id,
              onTap: () => onSelect(template.id),
            ),
            const SizedBox(height: 8),
          ],
        ],
      ],
    );
  }
}

class _TemplateTile extends StatelessWidget {
  const _TemplateTile({
    required this.template,
    required this.isSelected,
    required this.onTap,
  });

  final PromptTemplateDto template;
  final bool isSelected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final subtitle = template.description?.isNotEmpty ?? false
        ? template.description!
        : '${promptTypeLabels[template.type] ?? template.type} · ${template.scope}';
    return ListTile(
      selected: isSelected,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      tileColor: isSelected
          ? Theme.of(context).colorScheme.secondaryContainer
          : null,
      isThreeLine: (template.description?.isNotEmpty ?? false),
      title: Row(
        children: [
          Flexible(child: Text(template.name, overflow: TextOverflow.ellipsis)),
          if (template.isBuiltin) ...[
            const SizedBox(width: 6),
            _Badge(label: '内置', color: Colors.teal),
          ],
          if (template.isRecommended) ...[
            const SizedBox(width: 6),
            _Badge(label: '推荐', color: Colors.deepOrange),
          ],
        ],
      ),
      subtitle: Text(
        subtitle,
        maxLines: 2,
        overflow: TextOverflow.ellipsis,
      ),
      onTap: onTap,
    );
  }
}

class _Badge extends StatelessWidget {
  const _Badge({required this.label, required this.color});

  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        label,
        style: TextStyle(fontSize: 11, color: color),
      ),
    );
  }
}

class _PreviewPanel extends StatelessWidget {
  const _PreviewPanel({
    required this.controller,
    required this.template,
    required this.variables,
    required this.variablesValid,
    required this.onVariablesChanged,
  });

  final PromptController controller;
  final PromptTemplateDto template;
  final TextEditingController variables;
  final bool variablesValid;
  final VoidCallback onVariablesChanged;

  @override
  Widget build(BuildContext context) {
    final state = controller.state;
    final result = state.renderResult;
    final activeVersion = state.versions.isEmpty
        ? null
        : state.versions.firstWhere(
            (version) => version.id == template.activeVersionId,
            orElse: () => state.versions.first,
          );
    final schema = activeVersion?.variablesSchema ?? const {};
    final requiredVariables = schema.entries
        .where((entry) => entry.value is Map && entry.value['required'] == true)
        .map((entry) => entry.key)
        .toList();
    return ListView(
      children: [
        Text(template.name, style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: 4),
        Text('类型：${promptTypeLabels[template.type] ?? template.type}'),
        Text('范围：${template.scope}'),
        if (template.description != null && template.description!.isNotEmpty)
          Text('描述：${template.description}'),
        Text('分类：${promptCategoryLabel(template.category)}'),
        if (template.isBuiltin) ...[
          const Text('内置模板'),
          if (template.builtinKey != null)
            SelectableText(
              'builtin_key: ${template.builtinKey}',
              style: Theme.of(context).textTheme.bodySmall,
            ),
        ],
        if (activeVersion != null) ...[
          const SizedBox(height: 12),
          Text('模板详情', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 4),
          Text('active version: v${activeVersion.version}'),
          if (requiredVariables.isNotEmpty) ...[
            const SizedBox(height: 6),
            Text('必填变量（${requiredVariables.length}）：'),
            const SizedBox(height: 4),
            Wrap(
              spacing: 6,
              runSpacing: 4,
              children: [
                for (final name in requiredVariables)
                  Chip(
                    label: Text(name),
                    visualDensity: VisualDensity.compact,
                    materialTapTargetSize:
                        MaterialTapTargetSize.shrinkWrap,
                  ),
              ],
            ),
          ],
          if (activeVersion.defaultValues.isNotEmpty) ...[
            const SizedBox(height: 10),
            Text('默认值：'),
            const SizedBox(height: 4),
            for (final entry in activeVersion.defaultValues.entries)
              Text('${entry.key}: ${entry.value}'),
          ],
          if (activeVersion.outputConstraints != null &&
              activeVersion.outputConstraints!.isNotEmpty) ...[
            const SizedBox(height: 10),
            Text('输出约束：'),
            const SizedBox(height: 4),
            SelectableText(activeVersion.outputConstraints!),
          ],
          if (activeVersion.negativePrompt != null &&
              activeVersion.negativePrompt!.isNotEmpty) ...[
            const SizedBox(height: 10),
            Text('禁止项：'),
            const SizedBox(height: 4),
            SelectableText(activeVersion.negativePrompt!),
          ],
          const SizedBox(height: 10),
          Wrap(
            spacing: 8,
            children: [
              OutlinedButton.icon(
                onPressed: () => _copy(
                  context,
                  jsonEncode({
                    'name': template.name,
                    'type': template.type,
                    'description': template.description,
                    'system_prompt': activeVersion.systemPrompt,
                    'role_prompt': activeVersion.rolePrompt,
                    'instruction_template':
                        activeVersion.instructionTemplate,
                    'negative_prompt': activeVersion.negativePrompt,
                    'output_constraints':
                        activeVersion.outputConstraints,
                    'variables_schema': activeVersion.variablesSchema,
                    'default_values': activeVersion.defaultValues,
                  }),
                  '模板已复制',
                ),
                icon: const Icon(Icons.copy_outlined),
                label: const Text('复制模板'),
              ),
              OutlinedButton.icon(
                onPressed: () => _copy(
                  context,
                  jsonEncode(activeVersion.variablesSchema),
                  '变量 schema 已复制',
                ),
                icon: const Icon(Icons.data_object),
                label: const Text('复制变量 schema'),
              ),
            ],
          ),
        ],
        const SizedBox(height: 12),
        Text('版本', style: Theme.of(context).textTheme.titleMedium),
        for (final version in state.versions)
          ListTile(
            dense: true,
            title: Text('v${version.version}'),
            subtitle: Text(version.changeNote ?? version.createdAt),
            trailing: template.activeVersionId == version.id
                ? const Icon(Icons.check_circle)
                : null,
          ),
        const SizedBox(height: 12),
        TextField(
          controller: variables,
          minLines: 4,
          maxLines: 8,
          onChanged: (_) => onVariablesChanged(),
          decoration: InputDecoration(
            labelText: '变量 JSON',
            border: const OutlineInputBorder(),
            errorText: variablesValid ? null : '必须是合法 JSON object',
          ),
        ),
        const SizedBox(height: 8),
        FilledButton.icon(
          onPressed: variablesValid
              ? () => controller.renderPreview(variablesJson: variables.text)
              : null,
          icon: const Icon(Icons.visibility_outlined),
          label: const Text('渲染预览'),
        ),
        const SizedBox(height: 16),
        if (result != null) ...[
          Text('已渲染提示词', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          SelectableText(result.renderedPrompt),
          const SizedBox(height: 8),
          OutlinedButton.icon(
            onPressed: () => _copy(
              context,
              result.renderedPrompt,
              '已渲染提示词已复制',
            ),
            icon: const Icon(Icons.copy_outlined),
            label: const Text('复制已渲染提示词'),
          ),
          if (result.missingVariables.isNotEmpty) ...[
            const SizedBox(height: 12),
            Text('缺失变量：${result.missingVariables.join(', ')}'),
          ],
          if (result.warnings.isNotEmpty) ...[
            const SizedBox(height: 12),
            Text('警告：${result.warnings.join('; ')}'),
          ],
          const SizedBox(height: 12),
          SelectableText('提示词哈希：${result.promptHash}'),
        ],
      ],
    );
  }

  void _copy(BuildContext context, String text, String message) {
    Clipboard.setData(ClipboardData(text: text));
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(message)));
  }
}
