import 'package:flutter/material.dart';

import '../models/memory_retrieval_result_dto.dart';

class MemoryContextPreviewPanel extends StatelessWidget {
  const MemoryContextPreviewPanel({super.key, required this.result});

  final MemoryRetrieveResultDto? result;

  @override
  Widget build(BuildContext context) {
    final text = result?.toRetrievedMemoryText() ?? '';
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              'Retrieved Memory Preview',
              style: TextStyle(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 8),
            SizedBox(
              height: 180,
              child: SingleChildScrollView(
                child: SelectableText(text.isEmpty ? '尚未检索 memory。' : text),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
