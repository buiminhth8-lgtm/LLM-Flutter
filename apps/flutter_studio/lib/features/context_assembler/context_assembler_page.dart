import 'package:flutter/material.dart';

import '../../core/ui/app_empty_state.dart';
import '../../core/ui/app_section_header.dart';
import 'context_controller.dart';
import 'widgets/context_budget_panel.dart';
import 'widgets/context_render_preview_panel.dart';
import 'widgets/context_selected_items_panel.dart';
import 'widgets/context_variables_panel.dart';
import 'widgets/context_warnings_panel.dart';

class ContextAssemblerPage extends StatefulWidget {
  const ContextAssemblerPage({super.key, required this.controller});

  final ContextController controller;

  @override
  State<ContextAssemblerPage> createState() => _ContextAssemblerPageState();
}

class _ContextAssemblerPageState extends State<ContextAssemblerPage> {
  final _goal = TextEditingController();
  final _targetLength = TextEditingController(text: '1200-1800 中文字符');
  final _maxTokens = TextEditingController(text: '4096');
  final _reservedOutput = TextEditingController(text: '1200');
  final _maxContext = TextEditingController(text: '2500');
  final _maxChars = TextEditingController(text: '12000');

  @override
  void dispose() {
    _goal.dispose();
    _targetLength.dispose();
    _maxTokens.dispose();
    _reservedOutput.dispose();
    _maxContext.dispose();
    _maxChars.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: widget.controller,
      builder: (context, _) => _buildContent(context),
    );
  }

  Widget _buildContent(BuildContext context) {
    final state = widget.controller.state;
    final budgetPanel = ContextBudgetPanel(
      maxTokens: _maxTokens,
      reservedOutputTokens: _reservedOutput,
      maxContextTokens: _maxContext,
      maxChars: _maxChars,
      result: state.result?.budget,
    );
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppSectionHeader(
            title: 'Context Preview',
            subtitle: 'Stage 3：选择、排序并按预算装配小说资料，不调用模型。',
            actions: [
              IconButton.filledTonal(
                onPressed: state.loading ? null : widget.controller.refresh,
                icon: const Icon(Icons.refresh),
                tooltip: 'Refresh',
              ),
            ],
          ),
          if (state.loading) const LinearProgressIndicator(),
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
          const SizedBox(height: 12),
          Expanded(
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                SizedBox(
                  width: 380,
                  child: ListView(
                    children: [
                      DropdownButtonFormField<String>(
                        initialValue: state.selectedProjectId,
                        items: [
                          for (final project in state.projects)
                            DropdownMenuItem(
                              value: project.id,
                              child: Text(project.title),
                            ),
                        ],
                        onChanged: widget.controller.selectProject,
                        decoration: const InputDecoration(
                          labelText: '小说项目',
                          border: OutlineInputBorder(),
                        ),
                      ),
                      const SizedBox(height: 8),
                      DropdownButtonFormField<String>(
                        initialValue: state.selectedChapterId,
                        items: [
                          for (final chapter in state.chapters)
                            DropdownMenuItem(
                              value: chapter.id,
                              child: Text(
                                '${chapter.chapterIndex}. ${chapter.title}',
                              ),
                            ),
                        ],
                        onChanged: widget.controller.selectChapter,
                        decoration: const InputDecoration(
                          labelText: '章节（可选）',
                          border: OutlineInputBorder(),
                        ),
                      ),
                      const SizedBox(height: 8),
                      DropdownButtonFormField<String>(
                        initialValue: state.selectedSceneId,
                        items: [
                          for (final scene in state.scenes)
                            DropdownMenuItem(
                              value: scene.id,
                              child: Text(scene.title),
                            ),
                        ],
                        onChanged: widget.controller.selectScene,
                        decoration: const InputDecoration(
                          labelText: '场景（可选）',
                          border: OutlineInputBorder(),
                        ),
                      ),
                      const SizedBox(height: 8),
                      DropdownButtonFormField<String>(
                        initialValue: state.selectedTemplateId,
                        items: [
                          for (final template in state.templates)
                            DropdownMenuItem(
                              value: template.id,
                              child: Text(template.name),
                            ),
                        ],
                        onChanged: widget.controller.selectTemplate,
                        decoration: const InputDecoration(
                          labelText: 'Prompt 模板（预览时需要）',
                          border: OutlineInputBorder(),
                        ),
                      ),
                      const SizedBox(height: 8),
                      TextField(
                        controller: _goal,
                        minLines: 2,
                        maxLines: 4,
                        decoration: const InputDecoration(
                          labelText: '当前章节目标',
                          border: OutlineInputBorder(),
                        ),
                      ),
                      const SizedBox(height: 8),
                      TextField(
                        controller: _targetLength,
                        decoration: const InputDecoration(
                          labelText: '目标长度',
                          border: OutlineInputBorder(),
                        ),
                      ),
                      const SizedBox(height: 14),
                      budgetPanel,
                      const SizedBox(height: 14),
                      Row(
                        children: [
                          Expanded(
                            child: FilledButton.icon(
                              onPressed:
                                  state.loading ||
                                      state.selectedProjectId == null
                                  ? null
                                  : () => widget.controller.assemble(
                                      budget: budgetPanel.value(),
                                      currentChapterGoal: _goal.text,
                                      targetLength: _targetLength.text,
                                    ),
                              icon: const Icon(Icons.account_tree_outlined),
                              label: const Text('Assemble'),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: OutlinedButton.icon(
                              onPressed:
                                  state.loading ||
                                      state.selectedProjectId == null ||
                                      state.selectedTemplateId == null
                                  ? null
                                  : () => widget.controller.assemble(
                                      budget: budgetPanel.value(),
                                      currentChapterGoal: _goal.text,
                                      targetLength: _targetLength.text,
                                      renderPreview: true,
                                    ),
                              icon: const Icon(Icons.preview_outlined),
                              label: const Text('Render Preview'),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                const VerticalDivider(width: 24),
                Expanded(
                  child: state.result == null
                      ? const AppEmptyState(
                          title: '尚未装配上下文',
                          message: '选择项目和预算后执行 Assemble。',
                          icon: Icons.account_tree_outlined,
                        )
                      : ListView(
                          children: [
                            ContextWarningsPanel(
                              warnings: state.result!.warnings,
                            ),
                            const Divider(height: 28),
                            ContextSelectedItemsPanel(
                              selectedItems: state.result!.selectedItems,
                            ),
                            const Divider(height: 28),
                            ContextVariablesPanel(
                              variables: state.result!.variables,
                            ),
                            if (state.preview != null) ...[
                              const Divider(height: 28),
                              ContextRenderPreviewPanel(
                                preview: state.preview!,
                              ),
                            ],
                          ],
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
