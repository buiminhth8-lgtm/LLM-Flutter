import 'package:flutter/material.dart';

class MemoryIndexStatusPanel extends StatelessWidget {
  const MemoryIndexStatusPanel({super.key, required this.status});

  final Map<String, dynamic> status;

  @override
  Widget build(BuildContext context) {
    if (status.isEmpty) {
      return const Text('Index status unavailable.');
    }
    final documents = Map<String, dynamic>.from(
      (status['documents'] as Map?) ?? {},
    );
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Index Status',
              style: TextStyle(fontWeight: FontWeight.w700),
            ),
            Text(
              'documents: ${documents['total'] ?? 0} active: ${documents['active'] ?? 0} stale: ${documents['stale'] ?? 0}',
            ),
            Text('chunks: ${status['chunks'] ?? 0}'),
            Text(
              'FTS5: ${status['fts_available'] == true ? 'available' : 'fallback keyword'}',
            ),
          ],
        ),
      ),
    );
  }
}
