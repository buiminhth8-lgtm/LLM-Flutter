import 'package:flutter/material.dart';

class RagPage extends StatelessWidget {
  const RagPage({super.key, required this.queryController, required this.result, required this.onQuery});

  final TextEditingController queryController;
  final String? result;
  final VoidCallback onQuery;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('RAG', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
          const SizedBox(height: 8),
          const Text('Upload and rebuild are backend job based. This page provides the minimum query test surface.'),
          const SizedBox(height: 12),
          Row(children: [
            Expanded(child: TextField(controller: queryController, decoration: const InputDecoration(labelText: 'RAG query', border: OutlineInputBorder()))),
            const SizedBox(width: 8),
            FilledButton.icon(onPressed: onQuery, icon: const Icon(Icons.search), label: const Text('Query')),
          ]),
          const SizedBox(height: 12),
          Expanded(child: Card(child: Padding(padding: const EdgeInsets.all(12), child: SingleChildScrollView(child: SelectableText(result ?? 'No query result yet.'))))),
        ],
      ),
    );
  }
}
