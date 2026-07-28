import 'package:flutter/material.dart';

class StoragePage extends StatelessWidget {
  const StoragePage({
    super.key,
    required this.storage,
    required this.cleanupPreview,
    required this.onRefresh,
    required this.onPreview,
    required this.onCleanup,
  });

  final Map<String, dynamic>? storage;
  final Map<String, dynamic>? cleanupPreview;
  final VoidCallback onRefresh;
  final VoidCallback onPreview;
  final VoidCallback onCleanup;

  @override
  Widget build(BuildContext context) {
    final categories = storage?['categories'] is List ? storage!['categories'] as List : const [];
    final items = cleanupPreview?['items'] is List ? cleanupPreview!['items'] as List : const [];
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          const Text('Storage', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
          const Spacer(),
          IconButton.filledTonal(onPressed: onRefresh, icon: const Icon(Icons.refresh), tooltip: 'Refresh'),
          const SizedBox(width: 8),
          OutlinedButton.icon(onPressed: onPreview, icon: const Icon(Icons.fact_check), label: const Text('Preview cleanup')),
          const SizedBox(width: 8),
          FilledButton.icon(onPressed: items.isEmpty ? null : onCleanup, icon: const Icon(Icons.cleaning_services), label: const Text('Cleanup')),
        ]),
        const SizedBox(height: 12),
        Expanded(
          child: Row(children: [
            Expanded(
              child: Card(
                child: ListView.separated(
                  padding: const EdgeInsets.all(8),
                  itemCount: categories.length,
                  separatorBuilder: (_, _) => const Divider(height: 1),
                  itemBuilder: (context, index) {
                    final map = categories[index] is Map ? categories[index] as Map : const {};
                    final cleanable = map['cleanable'] == true;
                    return ListTile(
                      leading: Icon(cleanable ? Icons.delete_sweep_outlined : Icons.lock_outline),
                      title: Text('${map['name'] ?? 'category'}'),
                      subtitle: Text('${map['size_bytes'] ?? 0} bytes${cleanable ? '' : ' - protected'}'),
                    );
                  },
                ),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Card(
                child: ListView.separated(
                  padding: const EdgeInsets.all(8),
                  itemCount: items.length,
                  separatorBuilder: (_, _) => const Divider(height: 1),
                  itemBuilder: (context, index) {
                    final map = items[index] is Map ? items[index] as Map : const {};
                    return ListTile(
                      leading: const Icon(Icons.preview_outlined),
                      title: Text('${map['category'] ?? 'cleanup item'}'),
                      subtitle: Text('${map['path'] ?? ''}\n${map['reason'] ?? ''} - ${map['size_bytes'] ?? 0} bytes'),
                    );
                  },
                ),
              ),
            ),
          ]),
        ),
      ]),
    );
  }
}
