import 'package:flutter/material.dart';
import 'package:flutter_studio/features/memory/models/memory_retrieval_result_dto.dart';
import 'package:flutter_studio/features/memory/widgets/memory_context_preview_panel.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('Memory context preview displays retrieved_memory text', (
    tester,
  ) async {
    final result = MemoryRetrieveResultDto.fromMap({
      'retrieval_id': 'ret-1',
      'project_id': 'p1',
      'chunks': [
        {
          'chunk_id': 'chunk-1',
          'document_id': 'doc-1',
          'source_type': 'world_entry',
          'source_id': 'w1',
          'title': '黑市',
          'text': '黑市位于旧城地下。',
          'score': 0.9,
        },
      ],
      'selected_chunks': ['chunk-1'],
    });

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: MemoryContextPreviewPanel(result: result)),
      ),
    );

    expect(find.textContaining('Retrieved Memory Preview'), findsOneWidget);
    expect(find.textContaining('黑市位于旧城地下'), findsOneWidget);
  });
}
