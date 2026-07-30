import 'package:flutter/material.dart';

class ContextSelectedItemsPanel extends StatelessWidget {
  const ContextSelectedItemsPanel({super.key, required this.selectedItems});

  final Map<String, List<String>> selectedItems;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('已选择资料', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 6),
        for (final entry in selectedItems.entries)
          Padding(
            padding: const EdgeInsets.only(bottom: 4),
            child: Text('${entry.key}: ${entry.value.length} 项'),
          ),
      ],
    );
  }
}
