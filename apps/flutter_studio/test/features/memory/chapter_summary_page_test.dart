import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_studio/core/api/api_client.dart';
import 'package:flutter_studio/features/memory/chapter_summary_page.dart';
import 'package:flutter_studio/features/memory/memory_api_client.dart';
import 'package:flutter_studio/features/memory/memory_controller.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

class ChapterSummaryHttpClient extends http.BaseClient {
  bool created = false;
  bool generated = false;

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    final path = request.url.path;
    Object body = <String, Object?>{};
    if (path.endsWith('/summaries') && request.method == 'GET') {
      body = {
        'data': [_summary()],
      };
    } else if (path.endsWith('/summaries') && request.method == 'POST') {
      created = true;
      body = _summary();
    } else if (path.endsWith('/summaries/generate')) {
      generated = true;
      body = _summary(generatedBy: 'model');
    } else if (path.endsWith('/activate')) {
      body = _summary();
    }
    return http.StreamedResponse(
      Stream.value(utf8.encode(jsonEncode(body))),
      200,
      headers: {'content-type': 'application/json'},
    );
  }

  Map<String, Object?> _summary({String generatedBy = 'manual'}) => {
    'summary_id': 'sum-1',
    'project_id': 'p1',
    'chapter_id': 'c1',
    'summary_type': 'short',
    'summary_text': '主角进入黑市。',
    'source_text_hash': 'hash',
    'generated_by': generatedBy,
    'status': 'active',
  };
}

void main() {
  testWidgets('Chapter Summary page creates and generates summaries', (
    tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(1000, 900));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    final httpClient = ChapterSummaryHttpClient();
    final controller = MemoryController(
      MemoryApiClient(
        LlmStudioClient('http://127.0.0.1:8000', httpClient: httpClient),
      ),
    );
    addTearDown(controller.dispose);

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: ChapterSummaryPage(controller: controller)),
      ),
    );
    await tester.enterText(
      find.byKey(const Key('memory-summary-chapter-id')),
      'c1',
    );
    await tester.enterText(
      find.byKey(const Key('memory-summary-text')),
      '主角进入黑市。',
    );
    await tester.tap(find.byKey(const Key('memory-create-summary')));
    await tester.pumpAndSettle();
    expect(httpClient.created, isTrue);
    await tester.enterText(
      find.byKey(const Key('memory-summary-model-id')),
      'm1',
    );
    await tester.tap(find.byKey(const Key('memory-generate-summary')));
    await tester.pumpAndSettle();
    expect(httpClient.generated, isTrue);
  });
}
