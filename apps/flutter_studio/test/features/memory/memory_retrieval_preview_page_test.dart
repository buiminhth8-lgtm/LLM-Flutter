import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_studio/core/api/api_client.dart';
import 'package:flutter_studio/features/memory/memory_api_client.dart';
import 'package:flutter_studio/features/memory/memory_controller.dart';
import 'package:flutter_studio/features/memory/memory_retrieval_preview_page.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

class RetrievalPreviewHttpClient extends http.BaseClient {
  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    Object body = <String, Object?>{};
    if (request.url.path == '/v1/memory/retrieve') {
      body = {
        'retrieval_id': 'ret-1',
        'project_id': 'p1',
        'query_text': '黑市',
        'chunks': [
          {
            'chunk_id': 'chunk-1',
            'document_id': 'doc-1',
            'source_type': 'world_entry',
            'source_id': 'w1',
            'title': '黑市',
            'text': '黑市位于旧城地下。',
            'score': 0.92,
          },
        ],
        'selected_chunks': ['chunk-1'],
      };
    }
    return http.StreamedResponse(
      Stream.value(utf8.encode(jsonEncode(body))),
      200,
      headers: {'content-type': 'application/json'},
    );
  }
}

void main() {
  testWidgets('Retrieval Preview displays chunks with score and source', (
    tester,
  ) async {
    final controller = MemoryController(
      MemoryApiClient(
        LlmStudioClient(
          'http://127.0.0.1:8000',
          httpClient: RetrievalPreviewHttpClient(),
        ),
      ),
    );
    addTearDown(controller.dispose);
    controller.state = controller.state.copyWith(selectedProjectId: 'p1');

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: MemoryRetrievalPreviewPage(controller: controller),
        ),
      ),
    );
    await tester.enterText(find.byKey(const Key('memory-query-text')), '黑市');
    await tester.tap(find.byKey(const Key('memory-retrieve')));
    await tester.pumpAndSettle();

    expect(find.textContaining('world_entry'), findsOneWidget);
    expect(find.textContaining('0.92'), findsOneWidget);
  });
}
