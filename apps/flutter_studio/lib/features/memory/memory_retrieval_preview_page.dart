import 'package:flutter/material.dart';

import 'memory_controller.dart';
import 'widgets/memory_retrieval_panel.dart';

class MemoryRetrievalPreviewPage extends StatefulWidget {
  const MemoryRetrievalPreviewPage({super.key, required this.controller});

  final MemoryController controller;

  @override
  State<MemoryRetrievalPreviewPage> createState() =>
      _MemoryRetrievalPreviewPageState();
}

class _MemoryRetrievalPreviewPageState
    extends State<MemoryRetrievalPreviewPage> {
  final _query = TextEditingController();
  final _topK = TextEditingController(text: '12');
  final _maxTokens = TextEditingController(text: '1200');

  @override
  void dispose() {
    _query.dispose();
    _topK.dispose();
    _maxTokens.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AnimatedBuilder(
    animation: widget.controller,
    builder: (context, _) => Padding(
      padding: const EdgeInsets.all(20),
      child: MemoryRetrievalPanel(
        result: widget.controller.state.retrievalResult,
        queryController: _query,
        topKController: _topK,
        maxTokensController: _maxTokens,
        onRetrieve: () => widget.controller.retrieve(
          queryText: _query.text,
          topK: int.tryParse(_topK.text) ?? 12,
          maxMemoryTokens: int.tryParse(_maxTokens.text) ?? 1200,
        ),
      ),
    ),
  );
}
