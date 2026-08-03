import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_studio/core/api/api_client.dart';
import 'package:flutter_studio/core/api/sse_client.dart';
import 'package:flutter_studio/features/memory/memory_api_client.dart';
import 'package:flutter_studio/features/writing/models/target_length_dto.dart';
import 'package:flutter_studio/features/writing/writing_api_client.dart';
import 'package:flutter_studio/features/writing/writing_controller.dart';
import 'package:flutter_studio/features/writing/writing_workspace_page.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

class WritingMemoryHttpClient extends http.BaseClient {
  Map<String, dynamic>? streamBody;
  bool retrieved = false;

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    if (request is http.Request && request.url.path == '/v1/writing/stream') {
      streamBody = jsonDecode(request.body) as Map<String, dynamic>;
      final events = [
        'data: {"type":"start","generation_id":"gen-1"}\n\n',
        'data: {"type":"done","generation_id":"gen-1","finish_reason":"stop","warnings":[]}\n\n',
      ].join();
      return http.StreamedResponse(
        Stream.value(utf8.encode(events)),
        200,
        headers: {'content-type': 'text/event-stream'},
      );
    }
    final path = request.url.path;
    Object body = <String, Object?>{};
    if (path == '/v1/novels/projects') {
      body = {
        'data': [
          {'id': 'p1', 'title': '长夜', 'slug': 'long-night', 'status': 'active'},
        ],
      };
    } else if (path == '/v1/novels/projects/p1/chapters') {
      body = {
        'data': [
          {'id': 'c1', 'project_id': 'p1', 'title': '黑市', 'chapter_index': 1},
        ],
      };
    } else if (path == '/v1/novels/chapters/c1/scenes') {
      body = {'data': <Object?>[]};
    } else if (path == '/v1/prompts/templates') {
      body = {
        'data': [
          {
            'id': 't1',
            'name': '章节生成',
            'type': 'chapter_generate',
            'scope': 'global',
          },
        ],
      };
    } else if (path == '/v1/models') {
      body = {
        'data': [
          {'id': 'm1', 'display_name': 'Qwen Local'},
        ],
      };
    } else if (path == '/v1/adapters') {
      body = {'data': <Object?>[]};
    } else if (path == '/v1/writing/generations') {
      body = {'data': <Object?>[]};
    } else if (path == '/v1/memory/retrieve') {
      retrieved = true;
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
            'score': 0.9,
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
  testWidgets('Writing Workspace shows Memory switch and sends memory config', (
    tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(1600, 1200));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    final httpClient = WritingMemoryHttpClient();
    final raw = LlmStudioClient(
      'http://127.0.0.1:8000',
      httpClient: httpClient,
      sseClient: SseClient(client: httpClient),
    );
    final controller = WritingController(
      WritingApiClient(raw),
      memoryApi: MemoryApiClient(raw),
    );
    addTearDown(controller.dispose);
    await controller.refresh();

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: WritingWorkspacePage(controller: controller)),
      ),
    );
    expect(find.byKey(const Key('writing-memory-enabled')), findsOneWidget);
    await tester.tap(find.byKey(const Key('writing-memory-enabled')));
    await tester.pumpAndSettle();
    await tester.enterText(
      find.byKey(const Key('writing-current-chapter-goal')),
      '进入黑市',
    );
    await tester.drag(find.byType(ListView).last, const Offset(0, -160));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('writing-show-retrieved-memory')));
    await tester.pumpAndSettle();
    expect(httpClient.retrieved, isTrue);
    expect(
      controller.state.memoryPreview?.chunks.single.text,
      contains('黑市位于旧城地下'),
    );

    await controller.generate(
      currentChapterGoal: '进入黑市',
      targetLength: const TargetLengthDto(min: 1, max: 100),
      temperature: 0.8,
      topP: 0.9,
      maxTokens: 64,
      repetitionPenalty: 1.1,
    );
    expect(httpClient.streamBody?['memory']['enabled'], isTrue);
    expect(httpClient.streamBody?['memory']['query_text'], '进入黑市');
  });
}
