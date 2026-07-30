import 'dart:async';
import 'dart:convert';

import 'package:flutter_studio/core/api/api_client.dart';
import 'package:flutter_studio/features/context_assembler/context_api_client.dart';
import 'package:flutter_studio/features/context_assembler/models/context_assembly_request_dto.dart';
import 'package:flutter_studio/core/errors/error_mapper.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

class ContextRequest {
  ContextRequest(this.method, this.path, this.body);

  final String method;
  final String path;
  final String body;
}

class ContextHttpClient extends http.BaseClient {
  final requests = <ContextRequest>[];

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    final body = request is http.Request ? request.body : '';
    requests.add(ContextRequest(request.method, request.url.path, body));
    Object response = <String, Object?>{};
    if (request.url.path == '/v1/context/assemble') {
      response = {
        'context_id': 'context-1',
        'project_id': 'project-1',
        'chapter_id': 'chapter-1',
        'mode': 'chapter_generate',
        'variables': {'project_title': 'Novel'},
        'selected_items': {
          'characters': ['character-1'],
        },
        'budget': {
          'max_tokens': 4096,
          'reserved_output_tokens': 1200,
          'max_context_tokens': 2500,
          'max_chars': 12000,
          'estimated_tokens': 120,
          'estimated_chars': 300,
        },
        'warnings': [
          {
            'code': 'CONTEXT_TRUNCATED',
            'message': 'trimmed',
            'affected': ['world_entries'],
          },
        ],
        'estimated_tokens': 120,
        'estimated_chars': 300,
        'context_hash': 'hash',
      };
    } else if (request.url.path == '/v1/context/render-preview') {
      response = {
        'project_id': 'project-1',
        'mode': 'chapter_generate',
        'variables': {'project_title': 'Novel'},
        'selected_items': <String, Object?>{},
        'budget': <String, Object?>{},
        'warnings': <Object?>[],
        'estimated_tokens': 120,
        'estimated_chars': 300,
        'context_hash': 'hash',
        'rendered_prompt': 'Rendered prompt',
        'missing_variables': <Object?>[],
        'render_warnings': <Object?>[],
        'prompt_hash': 'prompt-hash',
      };
    } else if (request.method == 'GET') {
      response = {'data': <Object?>[]};
    }
    return http.StreamedResponse(
      Stream.value(utf8.encode(jsonEncode(response))),
      200,
      headers: {'content-type': 'application/json'},
    );
  }
}

void main() {
  test(
    'Context API client sends stable assembly contract and parses result',
    () async {
      final httpClient = ContextHttpClient();
      final api = ContextApiClient(
        LlmStudioClient('http://127.0.0.1:8000', httpClient: httpClient),
      );

      final result = await api.assembleContext(
        const ContextAssemblyRequestDto(
          projectId: 'project-1',
          chapterId: 'chapter-1',
          userVariables: {'current_chapter_goal': 'Enter market'},
        ),
      );

      final request = httpClient.requests.single;
      expect(request.path, '/v1/context/assemble');
      final body = jsonDecode(request.body) as Map;
      expect(body['project_id'], 'project-1');
      expect(body['target_budget']['max_context_tokens'], 2500);
      expect(body['user_variables']['current_chapter_goal'], 'Enter market');
      expect(result.estimatedTokens, 120);
      expect(result.warnings.single.code, 'CONTEXT_TRUNCATED');
      expect(result.selectedItems['characters'], ['character-1']);
    },
  );

  test('Context render preview parses rendered prompt', () async {
    final httpClient = ContextHttpClient();
    final api = ContextApiClient(
      LlmStudioClient('http://127.0.0.1:8000', httpClient: httpClient),
    );

    final result = await api.renderContextPreview(
      const ContextAssemblyRequestDto(
        projectId: 'project-1',
        templateId: 'template-1',
      ),
    );

    expect(result.renderedPrompt, 'Rendered prompt');
    expect(result.promptHash, 'prompt-hash');
  });

  test('Context errors map to readable Chinese messages', () {
    expect(mapApiErrorMessage('CONTEXT_INVALID_BUDGET', ''), contains('预算'));
    expect(mapApiErrorMessage('CONTEXT_TRUNCATED', ''), contains('裁剪'));
  });
}
