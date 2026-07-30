import 'package:flutter/material.dart';

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
            title: 'Prompt Studio',
            subtitle:
                'Stage 2: template versions, variable validation, and render preview only. No model generation is connected.',
            actions: [
              IconButton.filledTonal(
                onPressed: widget.controller.refresh,
                icon: const Icon(Icons.refresh),
                tooltip: 'Refresh',
              ),
              FilledButton.icon(
                onPressed: widget.controller.ensureDefaults,
                icon: const Icon(Icons.library_add_outlined),
                label: const Text('Ensure defaults'),
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
                  child: const Text('Dismiss'),
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
                        'Create template',
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
                          labelText: 'variables_schema JSON',
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
                          labelText: 'default_values JSON',
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
                        label: const Text('Create template'),
                      ),
                    ],
                  ),
                ),
                const VerticalDivider(width: 24),
                Expanded(
                  child: selected == null
                      ? const AppEmptyState(
                          title: 'No prompt template',
                          message: 'Create or ensure default templates first.',
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
        title: 'No templates',
        message: 'Use Ensure defaults or create a prompt template.',
        icon: Icons.description_outlined,
      );
    }
    return ListView.separated(
      itemCount: templates.length,
      separatorBuilder: (_, _) => const SizedBox(height: 8),
      itemBuilder: (context, index) {
        final template = templates[index];
        final isSelected = template.id == selected?.id;
        return ListTile(
          selected: isSelected,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
          tileColor: isSelected
              ? Theme.of(context).colorScheme.secondaryContainer
              : null,
          title: Text(template.name),
          subtitle: Text(
            '${promptTypeLabels[template.type] ?? template.type} · ${template.scope}',
          ),
          onTap: () => onSelect(template.id),
        );
      },
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
    return ListView(
      children: [
        Text(template.name, style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: 4),
        Text('Type: ${promptTypeLabels[template.type] ?? template.type}'),
        Text('Scope: ${template.scope}'),
        const SizedBox(height: 12),
        Text('Versions', style: Theme.of(context).textTheme.titleMedium),
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
            labelText: 'variables JSON',
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
          label: const Text('Render preview'),
        ),
        const SizedBox(height: 16),
        if (result != null) ...[
          Text(
            'Rendered prompt',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 8),
          SelectableText(result.renderedPrompt),
          if (result.missingVariables.isNotEmpty) ...[
            const SizedBox(height: 12),
            Text('Missing variables: ${result.missingVariables.join(', ')}'),
          ],
          if (result.warnings.isNotEmpty) ...[
            const SizedBox(height: 12),
            Text('Warnings: ${result.warnings.join('; ')}'),
          ],
          const SizedBox(height: 12),
          SelectableText('prompt_hash: ${result.promptHash}'),
        ],
      ],
    );
  }
}
