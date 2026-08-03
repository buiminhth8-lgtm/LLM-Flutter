import 'package:flutter/material.dart';

import '../models/memory_retrieval_result_dto.dart';
import 'memory_chunk_result_list.dart';

class MemoryRetrievalPanel extends StatelessWidget {
  const MemoryRetrievalPanel({
    super.key,
    required this.result,
    required this.queryController,
    required this.topKController,
    required this.maxTokensController,
    required this.onRetrieve,
    this.onEvaluateRetrieval,
  });

  final MemoryRetrieveResultDto? result;
  final TextEditingController queryController;
  final TextEditingController topKController;
  final TextEditingController maxTokensController;
  final VoidCallback onRetrieve;
  final ValueChanged<String>? onEvaluateRetrieval;

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      TextField(
        key: const Key('memory-query-text'),
        controller: queryController,
        minLines: 2,
        maxLines: 4,
        decoration: const InputDecoration(
          labelText: '查询文本',
          border: OutlineInputBorder(),
        ),
      ),
      const SizedBox(height: 8),
      Row(
        children: [
          Expanded(
            child: TextField(
              key: const Key('memory-top-k'),
              controller: topKController,
              decoration: const InputDecoration(
                labelText: 'top_k',
                border: OutlineInputBorder(),
              ),
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: TextField(
              key: const Key('memory-max-tokens'),
              controller: maxTokensController,
              decoration: const InputDecoration(
                labelText: '最大记忆 Token 数',
                border: OutlineInputBorder(),
              ),
            ),
          ),
        ],
      ),
      const SizedBox(height: 8),
      Row(
        children: [
          Expanded(
            child: FilledButton.icon(
              key: const Key('memory-retrieve'),
              onPressed: onRetrieve,
              icon: const Icon(Icons.search),
              label: const Text('检索'),
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: OutlinedButton.icon(
              key: const Key('memory-evaluate-retrieval'),
              onPressed:
                  result?.retrievalId == null || onEvaluateRetrieval == null
                  ? null
                  : () => onEvaluateRetrieval?.call(result!.retrievalId!),
              icon: const Icon(Icons.fact_check_outlined),
              label: const Text('评估'),
            ),
          ),
        ],
      ),
      const SizedBox(height: 8),
      if (result != null)
        Text(
          '检索：${result!.retrievalId ?? '-'} · 已选择 ${result!.selectedChunks.length} · Token ${result!.totalTokenEstimate}',
        ),
      Expanded(
        child: MemoryChunkResultList(chunks: result?.chunks ?? const []),
      ),
    ],
  );
}
