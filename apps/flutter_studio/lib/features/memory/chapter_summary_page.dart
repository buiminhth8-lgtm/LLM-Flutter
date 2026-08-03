import 'package:flutter/material.dart';

import 'memory_controller.dart';
import 'widgets/chapter_summary_editor.dart';

class ChapterSummaryPage extends StatefulWidget {
  const ChapterSummaryPage({super.key, required this.controller});

  final MemoryController controller;

  @override
  State<ChapterSummaryPage> createState() => _ChapterSummaryPageState();
}

class _ChapterSummaryPageState extends State<ChapterSummaryPage> {
  final _chapter = TextEditingController();
  final _summary = TextEditingController();
  final _model = TextEditingController();

  @override
  void dispose() {
    _chapter.dispose();
    _summary.dispose();
    _model.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AnimatedBuilder(
    animation: widget.controller,
    builder: (context, _) => Padding(
      padding: const EdgeInsets.all(20),
      child: ChapterSummaryEditor(
        chapterController: _chapter,
        summaryController: _summary,
        modelController: _model,
        summaries: widget.controller.state.summaries,
        onLoad: () => widget.controller.loadSummaries(_chapter.text.trim()),
        onCreate: () => widget.controller.createSummary(
          chapterId: _chapter.text.trim(),
          summaryText: _summary.text.trim(),
        ),
        onGenerate: () => widget.controller.generateSummary(
          chapterId: _chapter.text.trim(),
          modelId: _model.text.trim(),
        ),
        onActivate: (summaryId) =>
            widget.controller.activateSummary(_chapter.text.trim(), summaryId),
      ),
    ),
  );
}
