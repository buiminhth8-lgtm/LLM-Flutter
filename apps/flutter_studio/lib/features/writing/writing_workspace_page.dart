import 'dart:async';

import 'package:flutter/material.dart';

import '../../core/ui/app_section_header.dart';
import '../memory/widgets/memory_context_preview_panel.dart';
import '../memory/widgets/memory_source_filter_bar.dart';
import 'writing_controller.dart';
import 'writing_state.dart';
import 'widgets/writing_chapter_selector.dart';
import 'widgets/writing_context_preview_panel.dart';
import 'widgets/writing_generation_history_panel.dart';
import 'widgets/writing_generation_params_panel.dart';
import 'widgets/writing_model_selector.dart';
import 'widgets/writing_output_panel.dart';
import 'widgets/writing_project_selector.dart';
import 'widgets/writing_prompt_selector.dart';
import 'widgets/writing_target_length_panel.dart';

const writingModeLabels = <String, String>{
  'chapter_generate': '章节生成',
  'chapter_continue': '章节续写',
  'chapter_rewrite': '章节重写',
  'chapter_polish': '语言润色',
  'chapter_expand': '章节扩写',
  'dialogue_enhance': '对白增强',
  'scene_expand': '场景扩写',
  'summary_generate': '摘要生成',
  'custom': '自定义',
};

class WritingWorkspacePage extends StatefulWidget {
  const WritingWorkspacePage({
    super.key,
    required this.controller,
    this.onOpenRevision,
    this.onEvaluateGeneration,
  });

  final WritingController controller;
  final ValueChanged<String>? onOpenRevision;
  final ValueChanged<String>? onEvaluateGeneration;

  @override
  State<WritingWorkspacePage> createState() => _WritingWorkspacePageState();
}

class _WritingWorkspacePageState extends State<WritingWorkspacePage> {
  final _goal = TextEditingController();
  final _temperature = TextEditingController(text: '0.8');
  final _topP = TextEditingController(text: '0.9');
  final _maxTokens = TextEditingController(text: '2048');
  final _repetitionPenalty = TextEditingController(text: '1.1');
  final _minimum = TextEditingController(text: '1200');
  final _maximum = TextEditingController(text: '1800');
  final _memoryTopK = TextEditingController(text: '12');
  final _memoryMaxTokens = TextEditingController(text: '1200');
  String _unit = 'chars';
  String _strategy = 'soft';

  @override
  void initState() {
    super.initState();
    if (widget.controller.state.projects.isEmpty) {
      unawaited(widget.controller.refresh());
    }
  }

  @override
  void dispose() {
    _goal.dispose();
    _temperature.dispose();
    _topP.dispose();
    _maxTokens.dispose();
    _repetitionPenalty.dispose();
    _minimum.dispose();
    _maximum.dispose();
    _memoryTopK.dispose();
    _memoryMaxTokens.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AnimatedBuilder(
    animation: widget.controller,
    builder: (context, _) => _buildContent(context),
  );

  Widget _buildContent(BuildContext context) {
    final state = widget.controller.state;
    final targetPanel = WritingTargetLengthPanel(
      minimum: _minimum,
      maximum: _maximum,
      unit: _unit,
      strategy: _strategy,
      onUnitChanged: (value) => setState(() => _unit = value),
      onStrategyChanged: (value) => setState(() => _strategy = value),
    );
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppSectionHeader(
            title: '写作工作区',
            subtitle:
                '阶段 4：复用 ContextAssembler、PromptRenderer 与本地 Runtime 生成小说草稿。',
            actions: [
              IconButton.filledTonal(
                onPressed: state.loading ? null : widget.controller.refresh,
                icon: const Icon(Icons.refresh),
                tooltip: '刷新',
              ),
            ],
          ),
          if (state.loading || state.generating || state.saving)
            const LinearProgressIndicator(),
          if (state.error != null)
            MaterialBanner(
              content: Text(state.error!),
              leading: const Icon(Icons.error_outline),
              actions: const [SizedBox.shrink()],
            ),
          if (state.notice != null)
            MaterialBanner(
              content: Text(state.notice!),
              leading: const Icon(Icons.info_outline),
              actions: const [SizedBox.shrink()],
            ),
          const SizedBox(height: 12),
          Expanded(
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                SizedBox(
                  width: 270,
                  child: ListView(
                    children: [
                      WritingProjectSelector(
                        projects: state.projects,
                        value: state.selectedProjectId,
                        onChanged: widget.controller.selectProject,
                      ),
                      const SizedBox(height: 10),
                      WritingChapterSelector(
                        chapters: state.chapters,
                        value: state.selectedChapterId,
                        onChanged: widget.controller.selectChapter,
                      ),
                      const SizedBox(height: 10),
                      DropdownButtonFormField<String>(
                        initialValue: state.selectedSceneId,
                        isExpanded: true,
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
                      const SizedBox(height: 14),
                      Text(
                        '当前章节草稿',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 8),
                      Container(
                        key: const Key('writing-chapter-draft'),
                        height: 260,
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          border: Border.all(
                            color: Theme.of(context).dividerColor,
                          ),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: SingleChildScrollView(
                          child: SelectableText(
                            state.draftContent.isEmpty
                                ? '当前章节还没有草稿。'
                                : state.draftContent,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                const VerticalDivider(width: 24),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Expanded(
                        flex: 3,
                        child: WritingOutputPanel(
                          output: state.output,
                          generating: state.generating,
                          saving: state.saving,
                          canSave:
                              state.activeGenerationId != null &&
                              state.selectedChapterId != null &&
                              state.output.isNotEmpty,
                          onStop: widget.controller.stop,
                          onSave: () => widget.controller.saveToChapter(),
                          onAppend: () =>
                              widget.controller.saveToChapter(append: true),
                          onEditAsRevision: _createRevisionFromActiveOutput,
                          onEvaluateGeneration: _evaluateActiveGeneration,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Expanded(
                        flex: 2,
                        child: SingleChildScrollView(
                          child: Column(
                            children: [
                              for (final warning in state.warnings)
                                ListTile(
                                  dense: true,
                                  leading: const Icon(
                                    Icons.warning_amber_outlined,
                                  ),
                                  title: Text(
                                    '${warning['code'] ?? 'WRITING_WARNING'}',
                                  ),
                                  subtitle: Text('${warning['message'] ?? ''}'),
                                ),
                              WritingGenerationHistoryPanel(
                                records: state.history,
                                onSelected: widget.controller.openGeneration,
                                revisionIdsByGeneration:
                                    state.revisionIdsByGeneration,
                                onCreateRevision: _createRevisionFromGeneration,
                                onViewRevision: widget.onOpenRevision,
                                onEvaluateGeneration:
                                    widget.onEvaluateGeneration,
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
                const VerticalDivider(width: 24),
                SizedBox(
                  width: 340,
                  child: ListView(
                    children: [
                      DropdownButtonFormField<String>(
                        key: const Key('writing-mode-selector'),
                        initialValue: state.mode,
                        items: [
                          for (final entry in writingModeLabels.entries)
                            DropdownMenuItem(
                              value: entry.key,
                              child: Text(entry.value),
                            ),
                        ],
                        onChanged: (value) {
                          if (value != null) {
                            widget.controller.selectMode(value);
                          }
                        },
                        decoration: const InputDecoration(
                          labelText: '写作模式',
                          border: OutlineInputBorder(),
                        ),
                      ),
                      const SizedBox(height: 10),
                      WritingPromptSelector(
                        templates: state.templates,
                        value: state.selectedTemplateId,
                        onChanged: widget.controller.selectTemplate,
                      ),
                      const SizedBox(height: 10),
                      WritingModelSelector(
                        models: state.models,
                        value: state.selectedModelId,
                        onChanged: widget.controller.selectModel,
                      ),
                      const SizedBox(height: 10),
                      DropdownButtonFormField<String>(
                        initialValue: state.selectedAdapterId,
                        isExpanded: true,
                        items: [
                          const DropdownMenuItem(
                            value: '',
                            child: Text('不使用 Adapter'),
                          ),
                          for (final adapter in state.adapters)
                            DropdownMenuItem(
                              value:
                                  '${adapter['id'] ?? adapter['adapter_id'] ?? ''}',
                              child: Text(
                                '${adapter['name'] ?? adapter['id'] ?? ''}',
                              ),
                            ),
                        ],
                        onChanged: widget.controller.selectAdapter,
                        decoration: const InputDecoration(
                          labelText: 'Adapter（可选）',
                          border: OutlineInputBorder(),
                        ),
                      ),
                      const SizedBox(height: 10),
                      TextField(
                        key: const Key('writing-current-chapter-goal'),
                        controller: _goal,
                        minLines: 3,
                        maxLines: 5,
                        decoration: const InputDecoration(
                          labelText: '当前章节目标',
                          hintText: '例如：主角进入黑市，第一次发现灵骨交易。',
                          border: OutlineInputBorder(),
                        ),
                      ),
                      const SizedBox(height: 14),
                      targetPanel,
                      const SizedBox(height: 14),
                      WritingGenerationParamsPanel(
                        temperature: _temperature,
                        topP: _topP,
                        maxTokens: _maxTokens,
                        repetitionPenalty: _repetitionPenalty,
                      ),
                      const SizedBox(height: 14),
                      OutlinedButton.icon(
                        key: const Key('writing-render-context'),
                        onPressed: state.loading || state.generating
                            ? null
                            : () => widget.controller.renderContextPreview(
                                currentChapterGoal: _goal.text,
                                targetLength: targetPanel.value(),
                                maxTokens: _int(_maxTokens, 2048),
                              ),
                        icon: const Icon(Icons.preview_outlined),
                        label: const Text('渲染上下文预览'),
                      ),
                      const SizedBox(height: 8),
                      FilledButton.icon(
                        key: const Key('writing-generate'),
                        onPressed: state.generating
                            ? null
                            : () => widget.controller.generate(
                                currentChapterGoal: _goal.text,
                                targetLength: targetPanel.value(),
                                temperature: _double(_temperature, 0.8),
                                topP: _double(_topP, 0.9),
                                maxTokens: _int(_maxTokens, 2048),
                                repetitionPenalty: _double(
                                  _repetitionPenalty,
                                  1.1,
                                ),
                              ),
                        icon: const Icon(Icons.auto_awesome),
                        label: const Text('生成'),
                      ),
                      const SizedBox(height: 14),
                      _buildMemoryPanel(state),
                      const SizedBox(height: 8),
                      WritingContextPreviewPanel(preview: state.contextPreview),
                      const SizedBox(height: 8),
                      MemoryContextPreviewPanel(result: state.memoryPreview),
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

  static int _int(TextEditingController controller, int fallback) =>
      int.tryParse(controller.text.trim()) ?? fallback;

  static double _double(TextEditingController controller, double fallback) =>
      double.tryParse(controller.text.trim()) ?? fallback;

  Widget _buildMemoryPanel(WritingState state) => Card(
    child: Padding(
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          SwitchListTile(
            key: const Key('writing-memory-enabled'),
            contentPadding: EdgeInsets.zero,
            value: state.memoryEnabled,
            title: const Text('记忆 / RAG'),
            subtitle: const Text('开启后由后端 ContextAssembler 注入 retrieved_memory'),
            onChanged: widget.controller.setMemoryEnabled,
          ),
          Row(
            children: [
              Expanded(
                child: TextField(
                  key: const Key('writing-memory-top-k'),
                  controller: _memoryTopK,
                  enabled: state.memoryEnabled,
                  decoration: const InputDecoration(
                    labelText: '记忆 top_k',
                    border: OutlineInputBorder(),
                  ),
                  onChanged: (value) => widget.controller.setMemoryTopK(
                    int.tryParse(value.trim()) ?? 12,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: TextField(
                  key: const Key('writing-memory-max-tokens'),
                  controller: _memoryMaxTokens,
                  enabled: state.memoryEnabled,
                  decoration: const InputDecoration(
                    labelText: '最大 Token 数',
                    border: OutlineInputBorder(),
                  ),
                  onChanged: (value) => widget.controller.setMemoryMaxTokens(
                    int.tryParse(value.trim()) ?? 1200,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Wrap(
            spacing: 6,
            runSpacing: 4,
            children: [
              for (final entry in memorySourceTypeLabels.entries.take(6))
                FilterChip(
                  label: Text(entry.value),
                  selected: state.memorySourceTypes.contains(entry.key),
                  onSelected: state.memoryEnabled
                      ? (value) => widget.controller.toggleMemorySourceType(
                          entry.key,
                          value,
                        )
                      : null,
                ),
            ],
          ),
          const SizedBox(height: 8),
          OutlinedButton.icon(
            key: const Key('writing-show-retrieved-memory'),
            onPressed: state.memoryEnabled
                ? () => widget.controller.retrieveMemoryPreview(_goal.text)
                : null,
            icon: const Icon(Icons.search),
            label: const Text('显示检索记忆'),
          ),
        ],
      ),
    ),
  );

  Future<void> _createRevisionFromGeneration(String generationId) async {
    final revisionId = await widget.controller.createRevisionFromGeneration(
      generationId,
    );
    if (revisionId != null) {
      widget.onOpenRevision?.call(revisionId);
    }
  }

  Future<void> _createRevisionFromActiveOutput() async {
    final generationId = widget.controller.state.activeGenerationId;
    if (generationId == null) {
      return;
    }
    final revisionId = await widget.controller.createRevisionFromGeneration(
      generationId,
      editedText: widget.controller.state.output,
    );
    if (revisionId != null) {
      widget.onOpenRevision?.call(revisionId);
    }
  }

  void _evaluateActiveGeneration() {
    final generationId = widget.controller.state.activeGenerationId;
    if (generationId == null) {
      return;
    }
    widget.onEvaluateGeneration?.call(generationId);
  }
}
