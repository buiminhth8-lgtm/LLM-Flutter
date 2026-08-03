import 'package:flutter/material.dart';

import '../models/memory_chunk_dto.dart';

class MemoryChunkResultList extends StatelessWidget {
  const MemoryChunkResultList({super.key, required this.chunks});

  final List<MemoryChunkDto> chunks;

  @override
  Widget build(BuildContext context) => ListView(
    key: const Key('memory-chunk-result-list'),
    children: [
      if (chunks.isEmpty)
        const ListTile(title: Text('没有检索结果。'))
      else
        for (final chunk in chunks)
          Card(
            child: ListTile(
              title: Text('${chunk.sourceType} / ${chunk.title}'),
              subtitle: Text(
                chunk.text,
                maxLines: 5,
                overflow: TextOverflow.ellipsis,
              ),
              trailing: Text(chunk.score.toStringAsFixed(2)),
            ),
          ),
    ],
  );
}
