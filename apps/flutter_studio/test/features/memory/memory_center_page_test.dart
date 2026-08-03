import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_studio/app/app_routes.dart';
import 'package:flutter_studio/core/api/api_client.dart';
import 'package:flutter_studio/features/memory/memory_api_client.dart';
import 'package:flutter_studio/features/memory/memory_center_page.dart';
import 'package:flutter_studio/features/memory/memory_controller.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

class MemoryPageHttpClient extends http.BaseClient {
  bool built = false;
  bool rebuilt = false;

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    final path = request.url.path;
    Object body = <String, Object?>{};
    if (path == '/v1/memory/documents') {
      body = {
        'data': [
          {
            'document_id': 'doc-1',
            'project_id': 'p1',
            'source_type': 'world_entry',
            'source_id': 'w1',
            'title': '黑市',
            'content': '黑市位于旧城地下。',
            'tags': ['地点'],
            'priority': 10,
            'status': 'active',
            'metadata': <String, Object?>{},
          },
        ],
      };
    } else if (path == '/v1/memory/retrieval-records') {
      body = {'data': <Object?>[]};
    } else if (path.endsWith('/index/status')) {
      body = {
        'documents': {'total': 1, 'active': 1, 'stale': 0},
        'chunks': 1,
        'fts_available': true,
      };
    } else if (path.endsWith('/build-from-novel')) {
      built = true;
      body = {
        'project_id': 'p1',
        'documents_created': 1,
        'document_ids': ['doc-1'],
      };
    } else if (path.endsWith('/index/rebuild')) {
      rebuilt = true;
      body = {'project_id': 'p1', 'chunks_indexed': 1};
    }
    return http.StreamedResponse(
      Stream.value(utf8.encode(jsonEncode(body))),
      200,
      headers: {'content-type': 'application/json'},
    );
  }
}

void main() {
  testWidgets('Memory Center shows documents and triggers build/rebuild', (
    tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(1500, 1000));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    final httpClient = MemoryPageHttpClient();
    final controller = MemoryController(
      MemoryApiClient(
        LlmStudioClient('http://127.0.0.1:8000', httpClient: httpClient),
      ),
    );
    addTearDown(controller.dispose);
    await controller.setFilters(projectId: 'p1');

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: MemoryCenterPage(controller: controller)),
      ),
    );

    expect(find.text('黑市'), findsWidgets);
    await tester.tap(find.byKey(const Key('memory-build-from-novel')));
    await tester.pumpAndSettle();
    expect(httpClient.built, isTrue);
    await tester.tap(find.byKey(const Key('memory-rebuild-index')));
    await tester.pumpAndSettle();
    expect(httpClient.rebuilt, isTrue);
  });

  testWidgets('novel_rag_memory capability flag controls navigation entry', (
    tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(900, 1300));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: buildShellNavigation(
            selectedIndex: 0,
            onSelected: (_) {},
            showNovelStudio: true,
            showMemoryCenter: false,
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('Memory'), findsNothing);

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: buildShellNavigation(
            selectedIndex: 0,
            onSelected: (_) {},
            showNovelStudio: true,
            showMemoryCenter: true,
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('Memory'), findsOneWidget);
  });
}
