import 'dart:async';

import 'package:flutter/material.dart';

import '../../core/ui/app_section_header.dart';
import 'memory_controller.dart';
import 'widgets/chapter_summary_editor.dart';
import 'widgets/memory_document_detail.dart';
import 'widgets/memory_document_list.dart';
import 'widgets/memory_index_status_panel.dart';
import 'widgets/memory_retrieval_panel.dart';
import 'widgets/memory_source_filter_bar.dart';

class MemoryCenterPage extends StatefulWidget {
  const MemoryCenterPage({
    super.key,
    required this.controller,
    this.onEvaluateRetrieval,
  });

  final MemoryController controller;
  final ValueChanged<String>? onEvaluateRetrieval;

  @override
  State<MemoryCenterPage> createState() => _MemoryCenterPageState();
}

class _MemoryCenterPageState extends State<MemoryCenterPage> {
  final _project = TextEditingController();
  final _manualTitle = TextEditingController(text: '手动记忆');
  final _manualContent = TextEditingController();
  final _query = TextEditingController();
  final _topK = TextEditingController(text: '12');
  final _maxMemoryTokens = TextEditingController(text: '1200');
  final _chapter = TextEditingController();
  final _summary = TextEditingController();
  final _model = TextEditingController();

  @override
  void initState() {
    super.initState();
    if (widget.controller.state.selectedProjectId != null) {
      _project.text = widget.controller.state.selectedProjectId!;
      unawaited(widget.controller.refresh());
    }
  }

  @override
  void dispose() {
    _project.dispose();
    _manualTitle.dispose();
    _manualContent.dispose();
    _query.dispose();
    _topK.dispose();
    _maxMemoryTokens.dispose();
    _chapter.dispose();
    _summary.dispose();
    _model.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AnimatedBuilder(
    animation: widget.controller,
    builder: (context, _) {
      final state = widget.controller.state;
      return Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            AppSectionHeader(
              title: '记忆 / RAG 中心',
              subtitle: '阶段 10：管理长篇小说记忆、检索预览、章节摘要版本与 ContextAssembler 注入。',
              actions: [
                IconButton.filledTonal(
                  onPressed: state.loading ? null : widget.controller.refresh,
                  icon: const Icon(Icons.refresh),
                  tooltip: '刷新',
                ),
              ],
            ),
            if (state.loading || state.saving) const LinearProgressIndicator(),
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
                  SizedBox(width: 320, child: _buildLeftPane()),
                  const VerticalDivider(width: 24),
                  Expanded(
                    child: MemoryDocumentDetail(
                      document: state.currentDocument,
                    ),
                  ),
                  const VerticalDivider(width: 24),
                  SizedBox(width: 420, child: _buildRightPane()),
                ],
              ),
            ),
          ],
        ),
      );
    },
  );

  Widget _buildLeftPane() {
    final state = widget.controller.state;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        MemorySourceFilterBar(
          projectController: _project,
          sourceType: state.sourceType,
          status: state.status,
          onApply: (projectId, sourceType, status) =>
              widget.controller.setFilters(
                projectId: projectId.isEmpty ? null : projectId,
                sourceType: sourceType,
                status: status,
                clearProject: projectId.isEmpty,
                clearSourceType: sourceType == null,
              ),
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(
              child: FilledButton(
                key: const Key('memory-build-from-novel'),
                onPressed: widget.controller.buildFromNovel,
                child: const Text('从小说资料构建'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),
        OutlinedButton.icon(
          key: const Key('memory-rebuild-index'),
          onPressed: widget.controller.rebuildIndex,
          icon: const Icon(Icons.refresh),
          label: const Text('重建索引'),
        ),
        const SizedBox(height: 8),
        MemoryIndexStatusPanel(status: state.indexStatus),
        const SizedBox(height: 8),
        OutlinedButton.icon(
          key: const Key('memory-create-manual-note'),
          onPressed: _showManualNoteDialog,
          icon: const Icon(Icons.note_add_outlined),
          label: const Text('创建手动记忆笔记'),
        ),
        const SizedBox(height: 8),
        Expanded(
          child: MemoryDocumentList(
            documents: state.documents,
            currentDocumentId: state.currentDocument?.documentId,
            onSelect: widget.controller.selectDocument,
          ),
        ),
      ],
    );
  }

  Widget _buildRightPane() {
    final state = widget.controller.state;
    return DefaultTabController(
      length: 2,
      child: Column(
        children: [
          const TabBar(
            tabs: [
              Tab(text: '检索预览'),
              Tab(text: '章节摘要'),
            ],
          ),
          const SizedBox(height: 8),
          Expanded(
            child: TabBarView(
              children: [
                MemoryRetrievalPanel(
                  result: state.retrievalResult,
                  queryController: _query,
                  topKController: _topK,
                  maxTokensController: _maxMemoryTokens,
                  onRetrieve: () => widget.controller.retrieve(
                    queryText: _query.text,
                    topK: int.tryParse(_topK.text.trim()) ?? 12,
                    maxMemoryTokens:
                        int.tryParse(_maxMemoryTokens.text.trim()) ?? 1200,
                  ),
                  onEvaluateRetrieval: widget.onEvaluateRetrieval,
                ),
                ChapterSummaryEditor(
                  chapterController: _chapter,
                  summaryController: _summary,
                  modelController: _model,
                  summaries: state.summaries,
                  onLoad: () =>
                      widget.controller.loadSummaries(_chapter.text.trim()),
                  onCreate: () => widget.controller.createSummary(
                    chapterId: _chapter.text.trim(),
                    summaryText: _summary.text.trim(),
                  ),
                  onGenerate: () => widget.controller.generateSummary(
                    chapterId: _chapter.text.trim(),
                    modelId: _model.text.trim(),
                  ),
                  onActivate: (summaryId) => widget.controller.activateSummary(
                    _chapter.text.trim(),
                    summaryId,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 8),
          OutlinedButton.icon(
            onPressed: state.currentDocument == null
                ? null
                : widget.controller.archiveCurrent,
            icon: const Icon(Icons.archive_outlined),
            label: const Text('归档当前文档'),
          ),
        ],
      ),
    );
  }

  Future<void> _showManualNoteDialog() async {
    final projectId = _project.text.trim();
    await showDialog<void>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('创建手动记忆笔记'),
        content: SizedBox(
          width: 420,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: _manualTitle,
                decoration: const InputDecoration(labelText: '标题'),
              ),
              TextField(
                controller: _manualContent,
                minLines: 4,
                maxLines: 8,
                decoration: const InputDecoration(labelText: '内容'),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('取消'),
          ),
          FilledButton(
            onPressed: () {
              Navigator.of(context).pop();
              unawaited(
                widget.controller.createManualNote(
                  projectId: projectId,
                  title: _manualTitle.text.trim(),
                  content: _manualContent.text.trim(),
                ),
              );
            },
            child: const Text('创建'),
          ),
        ],
      ),
    );
  }
}
