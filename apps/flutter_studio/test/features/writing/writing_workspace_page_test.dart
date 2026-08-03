import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_studio/app/app_routes.dart';
import 'package:flutter_studio/core/api/api_client.dart';
import 'package:flutter_studio/core/api/sse_client.dart';
import 'package:flutter_studio/features/writing/writing_api_client.dart';
import 'package:flutter_studio/features/writing/writing_controller.dart';
import 'package:flutter_studio/features/writing/writing_workspace_page.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

class WritingPageHttpClient extends http.BaseClient {
  final List<String> requestPaths = [];
  bool saved = false;

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    requestPaths.add('${request.method} ${request.url.path}');
    final path = request.url.path;
    if (path == '/v1/writing/stream') {
      final events = [
        'data: {"type":"start","generation_id":"gen-1"}\n\n',
        'data: {"type":"delta","text":"夜色沉入旧城。"}\n\n',
        'data: {"type":"done","generation_id":"gen-1","finish_reason":"stop","warnings":[]}\n\n',
        'data: {"type":"end"}\n\n',
      ].join();
      return http.StreamedResponse(
        Stream.value(utf8.encode(events)),
        200,
        headers: {'content-type': 'text/event-stream'},
      );
    }
    Object response = <String, Object?>{};
    if (path == '/v1/novels/projects') {
      response = {
        'data': [
          {'id': 'p1', 'title': '长夜', 'slug': 'long-night', 'status': 'active'},
        ],
      };
    } else if (path == '/v1/novels/projects/p1/chapters') {
      response = {
        'data': [
          {
            'id': 'c1',
            'project_id': 'p1',
            'title': '黑市',
            'chapter_index': 1,
            'draft_content': saved ? '夜色沉入旧城。' : '旧稿',
            'word_count': saved ? 7 : 2,
            'status': 'draft',
          },
        ],
      };
    } else if (path == '/v1/novels/chapters/c1/scenes') {
      response = {'data': <Object?>[]};
    } else if (path == '/v1/prompts/templates') {
      response = {
        'data': [
          {
            'id': 't1',
            'name': '章节生成',
            'type': 'chapter_generate',
            'scope': 'global',
            'status': 'active',
          },
        ],
      };
    } else if (path == '/v1/models') {
      response = {
        'data': [
          {'id': 'm1', 'display_name': 'Qwen Local'},
        ],
      };
    } else if (path == '/v1/adapters') {
      response = {'data': <Object?>[]};
    } else if (path == '/v1/writing/generations') {
      response = {'data': <Object?>[]};
    } else if (path.endsWith('/save-to-chapter')) {
      saved = true;
      response = {'status': 'saved'};
    }
    return http.StreamedResponse(
      Stream.value(utf8.encode(jsonEncode(response))),
      200,
      headers: {'content-type': 'application/json'},
    );
  }
}

void main() {
  testWidgets('Writing Workspace streams output and saves it to draft', (
    tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(1600, 1100));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    final httpClient = WritingPageHttpClient();
    final raw = LlmStudioClient(
      'http://127.0.0.1:8000',
      httpClient: httpClient,
      sseClient: SseClient(client: httpClient),
    );
    final controller = WritingController(WritingApiClient(raw));
    addTearDown(controller.dispose);
    await controller.refresh();

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: WritingWorkspacePage(controller: controller)),
      ),
    );
    expect(find.text('旧稿'), findsOneWidget);
    expect(find.text('Qwen Local'), findsOneWidget);

    await tester.ensureVisible(find.byKey(const Key('writing-generate')));
    await tester.tap(find.byKey(const Key('writing-generate')));
    await tester.pumpAndSettle();
    expect(find.text('夜色沉入旧城。'), findsOneWidget);

    await tester.tap(find.byKey(const Key('writing-save-draft')));
    await tester.pumpAndSettle();
    expect(httpClient.saved, isTrue);
    expect(
      httpClient.requestPaths.any((path) => path.endsWith('/save-to-chapter')),
      isTrue,
    );
  });

  testWidgets('writing_workspace capability flag controls navigation entry', (
    tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(800, 1000));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: buildShellNavigation(
            selectedIndex: 0,
            onSelected: (_) {},
            showNovelStudio: true,
            showWritingWorkspace: false,
          ),
        ),
      ),
    );
    expect(find.text('写作'), findsNothing);

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: buildShellNavigation(
            selectedIndex: 0,
            onSelected: (_) {},
            showNovelStudio: true,
            showWritingWorkspace: true,
          ),
        ),
      ),
    );
    expect(find.text('写作'), findsOneWidget);
  });
}
