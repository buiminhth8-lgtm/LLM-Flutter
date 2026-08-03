import 'package:flutter/material.dart';

import '../models/memory_document_dto.dart';

class MemoryDocumentDetail extends StatelessWidget {
  const MemoryDocumentDetail({super.key, required this.document});

  final MemoryDocumentDto? document;

  @override
  Widget build(BuildContext context) {
    final item = document;
    if (item == null) {
      return const Center(child: Text('请选择记忆文档。'));
    }
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(item.title, style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 6),
            Text('${item.sourceType} / ${item.sourceId} · ${item.status}'),
            const SizedBox(height: 8),
            Wrap(
              spacing: 6,
              children: [for (final tag in item.tags) Chip(label: Text(tag))],
            ),
            const Divider(),
            Expanded(
              child: SingleChildScrollView(child: SelectableText(item.content)),
            ),
          ],
        ),
      ),
    );
  }
}
