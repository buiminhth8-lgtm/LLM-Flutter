import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_studio/app/app_routes.dart';
import 'package:flutter_studio/core/api/api_client.dart';
import 'package:flutter_studio/features/context_assembler/context_api_client.dart';
import 'package:flutter_studio/features/context_assembler/context_assembler_page.dart';
import 'package:flutter_studio/features/context_assembler/context_controller.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

class ContextPageHttpClient extends http.BaseClient {
  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    Object response = <String, Object?>{};
    if (request.url.path == '/v1/novels/projects') {
      response = {
        'data': [
          {'id': 'p1', 'title': 'Novel', 'slug': 'novel', 'status': 'active'},
        ],
      };
    } else if (request.url.path == '/v1/novels/projects/p1/chapters') {
      response = {
        'data': [
          {
            'id': 'c1',
            'project_id': 'p1',
            'title': '章节',
            'chapter_index': 1,
            'word_count': 0,
            'status': 'outline',
          },
        ],
      };
    } else if (request.url.path == '/v1/novels/chapters/c1/scenes') {
      response = {'data': <Object?>[]};
    } else if (request.url.path == '/v1/prompts/templates') {
      response = {
        'data': [
          {
            'id': 't1',
            'name': 'Template',
            'type': 'chapter_generate',
            'scope': 'global',
            'status': 'active',
          },
        ],
      };
    } else if (request.url.path == '/v1/context/assemble') {
      response = {
        'context_id': 'ctx',
        'project_id': 'p1',
        'chapter_id': 'c1',
        'mode': 'chapter_generate',
        'variables': {'project_title': 'Novel', 'chapter_title': '章节'},
        'selected_items': {
          'characters': ['char-1'],
        },
        'budget': {
          'max_context_tokens': 2500,
          'estimated_tokens': 42,
          'estimated_chars': 100,
        },
        'warnings': <Object?>[],
        'estimated_tokens': 42,
        'estimated_chars': 100,
        'context_hash': 'hash',
      };
    }
    return http.StreamedResponse(
      Stream.value(utf8.encode(jsonEncode(response))),
      200,
      headers: {'content-type': 'application/json'},
    );
  }
}

void main() {
  testWidgets('Context page selects project and renders assembled variables', (
    tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(1400, 1000));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    final controller = ContextController(
      ContextApiClient(
        LlmStudioClient(
          'http://127.0.0.1:8000',
          httpClient: ContextPageHttpClient(),
        ),
      ),
    );
    addTearDown(controller.dispose);
    await controller.refresh();

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: ContextAssemblerPage(controller: controller)),
      ),
    );
    await tester.tap(find.text('装配'));
    await tester.pumpAndSettle();

    expect(find.textContaining('project_title'), findsOneWidget);
    expect(find.textContaining('42 Token'), findsOneWidget);
    expect(find.text('未发生截断或预算警告。'), findsOneWidget);
  });

  testWidgets('Context navigation is capability-gated by caller flag', (
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
            showPromptStudio: true,
            showContextAssembler: false,
          ),
        ),
      ),
    );
    expect(find.text('上下文预览'), findsNothing);

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: buildShellNavigation(
            selectedIndex: 0,
            onSelected: (_) {},
            showNovelStudio: true,
            showPromptStudio: true,
            showContextAssembler: true,
          ),
        ),
      ),
    );
    expect(find.text('上下文预览'), findsOneWidget);
  });
}
