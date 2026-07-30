import 'dart:async';
import 'dart:convert';

import 'package:flutter_studio/core/api/api_client.dart';
import 'package:flutter_studio/features/prompt_studio/prompt_api_client.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

class CapturedPromptRequest {
  CapturedPromptRequest(this.method, this.path, this.body);

  final String method;
  final String path;
  final String body;
}

class PromptHttpClient extends http.BaseClient {
  final requests = <CapturedPromptRequest>[];

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    final body = request is http.Request ? request.body : '';
    requests.add(CapturedPromptRequest(request.method, request.url.path, body));
    Object responseBody = <String, Object?>{};
    if (request.method == 'GET') {
      responseBody = {'data': <Object?>[]};
    }
    if (request.url.path == '/v1/prompts/templates' &&
        request.method == 'POST') {
      responseBody = {
        'id': 'template-1',
        'name': 'Template',
        'type': 'chapter_generate',
        'scope': 'global',
        'status': 'active',
        'active_version_id': 'version-1',
      };
    }
    if (request.url.path == '/v1/prompts/render' && request.method == 'POST') {
      responseBody = {
        'template_id': 'template-1',
        'template_version_id': 'version-1',
        'rendered_prompt': 'Rendered',
        'missing_variables': ['chapter_outline'],
        'warnings': <Object?>[],
        'prompt_hash': 'abc',
      };
    }
    return http.StreamedResponse(
      Stream.value(utf8.encode(jsonEncode(responseBody))),
      200,
      headers: {'content-type': 'application/json'},
    );
  }
}

void main() {
  test('Prompt API client uses stable paths and body fields', () async {
    final httpClient = PromptHttpClient();
    final api = PromptApiClient(
      LlmStudioClient('http://127.0.0.1:8000', httpClient: httpClient),
    );

    await api.listTemplates();
    await api.createTemplate(
      name: 'Template',
      type: 'chapter_generate',
      instructionTemplate: 'Hello {{project_title}}',
      variablesSchema: {
        'project_title': {'type': 'string', 'required': true},
      },
      defaultValues: const {},
    );
    await api.render(
      templateId: 'template-1',
      variables: {'project_title': 'Novel'},
    );

    expect(httpClient.requests[0].path, '/v1/prompts/templates');
    expect(httpClient.requests[1].method, 'POST');
    final createBody = jsonDecode(httpClient.requests[1].body) as Map;
    expect(createBody['type'], 'chapter_generate');
    expect(createBody['instruction_template'], contains('{{project_title}}'));
    expect(httpClient.requests[2].path, '/v1/prompts/render');
    final renderBody = jsonDecode(httpClient.requests[2].body) as Map;
    expect(renderBody['template_id'], 'template-1');
    expect(renderBody['variables']['project_title'], 'Novel');
  });

  test('Prompt DTO parses render result missing variables', () async {
    final httpClient = PromptHttpClient();
    final api = PromptApiClient(
      LlmStudioClient('http://127.0.0.1:8000', httpClient: httpClient),
    );

    final result = await api.render(
      templateId: 'template-1',
      variables: const {},
    );

    expect(result.renderedPrompt, 'Rendered');
    expect(result.missingVariables, ['chapter_outline']);
  });
}
