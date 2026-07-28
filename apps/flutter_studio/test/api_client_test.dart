import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_studio/core/errors/error_mapper.dart';
import 'package:flutter_studio/main.dart';

class CapturedRequest {
  CapturedRequest(this.method, this.url, this.body);

  final String method;
  final Uri url;
  final String body;
}

class CapturingHttpClient extends http.BaseClient {
  CapturingHttpClient({this.responseBody = const {'status': 'ok'}});

  final Map<String, Object?> responseBody;
  final requests = <CapturedRequest>[];

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    final body = request is http.Request ? request.body : '';
    requests.add(CapturedRequest(request.method, request.url, body));
    return http.StreamedResponse(
      Stream.value(utf8.encode(jsonEncode(responseBody))),
      200,
      headers: {'content-type': 'application/json'},
    );
  }
}

void main() {
  test('API client sends stored API key as bearer and legacy headers', () {
    final client = LlmStudioClient('http://127.0.0.1:8000')
      ..userId = 'admin'
      ..apiKey = 'sk-test-key';

    expect(client.authHeadersForTesting(), {
      'X-User-ID': 'admin',
      'X-API-Key': 'sk-test-key',
      'Authorization': 'Bearer sk-test-key',
    });
  });

  test('RAG query uses question payload expected by backend', () async {
    final httpClient = CapturingHttpClient();
    final client = LlmStudioClient('http://127.0.0.1:8000', httpClient: httpClient);

    await client.ragQuery('hello', topK: 7);

    final request = httpClient.requests.single;
    expect(request.url.path, '/v1/rag/query');
    final body = jsonDecode(request.body) as Map<String, dynamic>;
    expect(body['question'], 'hello');
    expect(body['top_k'], 7);
    expect(body.containsKey('query'), isFalse);
  });

  test('Adapter actions include model body', () async {
    final httpClient = CapturingHttpClient();
    final client = LlmStudioClient('http://127.0.0.1:8000', httpClient: httpClient);

    await client.loadAdapter('adapter-1', 'model-1');
    await client.activateAdapter('adapter-1', 'model-1');
    await client.deactivateAdapter('adapter-1', modelId: 'model-1');
    await client.unloadAdapter('adapter-1', modelId: 'model-1');

    for (final request in httpClient.requests) {
      final body = jsonDecode(request.body) as Map<String, dynamic>;
      expect(body['model'], 'model-1');
    }
    expect(httpClient.requests.map((request) => request.url.path), [
      '/v1/adapters/adapter-1/load',
      '/v1/adapters/adapter-1/activate',
      '/v1/adapters/adapter-1/deactivate',
      '/v1/adapters/adapter-1/unload',
    ]);
  });

  test('deleteModel sends explicit confirm query parameter', () async {
    final httpClient = CapturingHttpClient();
    final client = LlmStudioClient('http://127.0.0.1:8000', httpClient: httpClient);

    await client.deleteModel('model-1', confirm: true);
    await client.deleteModel('model-2', confirm: false);

    expect(httpClient.requests[0].method, 'DELETE');
    expect(httpClient.requests[0].url.queryParameters['confirm'], 'true');
    expect(httpClient.requests[1].url.queryParameters['confirm'], 'false');
  });

  test('P0 API contract error codes map to Chinese messages', () {
    expect(mapApiErrorMessage('ADAPTER_MODEL_REQUIRED', 'fallback'), contains('基础模型'));
    expect(mapApiErrorMessage('MODEL_DELETE_CONFIRM_REQUIRED', 'fallback'), contains('确认'));
    expect(mapApiErrorMessage('RAG_QUERY_INVALID', 'fallback'), contains('RAG'));
  });
}
