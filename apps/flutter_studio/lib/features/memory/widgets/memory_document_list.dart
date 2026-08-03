import 'package:flutter/material.dart';

import '../models/memory_document_dto.dart';

class MemoryDocumentList extends StatelessWidget {
  const MemoryDocumentList({
    super.key,
    required this.documents,
    this.currentDocumentId,
    required this.onSelect,
  });

  final List<MemoryDocumentDto> documents;
  final String? currentDocumentId;
  final ValueChanged<String> onSelect;

  @override
  Widget build(BuildContext context) => ListView(
    key: const Key('memory-document-list'),
    children: [
      if (documents.isEmpty)
        const ListTile(title: Text('没有 memory documents。'))
      else
        for (final document in documents)
          ListTile(
            selected: document.documentId == currentDocumentId,
            leading: const Icon(Icons.library_books_outlined),
            title: Text(document.title),
            subtitle: Text('${document.sourceType} · ${document.status}'),
            trailing: Text('${document.priority}'),
            onTap: () => onSelect(document.documentId),
          ),
    ],
  );
}
