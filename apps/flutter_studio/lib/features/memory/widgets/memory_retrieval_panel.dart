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
  });

  final MemoryRetrieveResultDto? result;
  final TextEditingController queryController;
  final TextEditingController topKController;
  final TextEditingController maxTokensController;
  final VoidCallback onRetrieve;

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
          labelText: 'Query Text',
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
                labelText: 'max memory tokens',
                border: OutlineInputBorder(),
              ),
            ),
          ),
        ],
      ),
      const SizedBox(height: 8),
      FilledButton.icon(
        key: const Key('memory-retrieve'),
        onPressed: onRetrieve,
        icon: const Icon(Icons.search),
        label: const Text('Retrieve'),
      ),
      const SizedBox(height: 8),
      if (result != null)
        Text(
          'retrieval: ${result!.retrievalId ?? '-'} · selected ${result!.selectedChunks.length} · tokens ${result!.totalTokenEstimate}',
        ),
      Expanded(
        child: MemoryChunkResultList(chunks: result?.chunks ?? const []),
      ),
    ],
  );
}
