import 'dart:async';
import 'dart:convert';

import 'package:flutter_studio/core/api/api_client.dart';
import 'package:flutter_studio/core/api/api_exception.dart';
import 'package:flutter_studio/core/api/sse_client.dart';
import 'package:flutter_studio/core/errors/error_mapper.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

class CapturedRequest {
  CapturedRequest(this.method, this.url, this.headers, this.body);

  final String method;
  final Uri url;
  final Map<String, String> headers;
  final String body;
}

class CapturingHttpClient extends http.BaseClient {
  CapturingHttpClient({
    this.responseBody = const {'status': 'ok'},
    this.statusCode = 200,
  });

  final Map<String, Object?> responseBody;
  final int statusCode;
  final requests = <CapturedRequest>[];

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    final body = request is http.Request ? request.body : '';
    requests.add(
      CapturedRequest(request.method, request.url, request.headers, body),
    );
    return http.StreamedResponse(
      Stream.value(utf8.encode(jsonEncode(responseBody))),
      statusCode,
      headers: {'content-type': 'application/json'},
    );
  }
}

class CapturingSseHttpClient extends http.BaseClient {
  final requests = <CapturedRequest>[];

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    final body = request is http.Request ? request.body : '';
    requests.add(
      CapturedRequest(request.method, request.url, request.headers, body),
    );
    return http.StreamedResponse(
      Stream.fromIterable([
        utf8.encode('data: {"choices":[{"delta":{"content":"ok"}}]}\n\n'),
        utf8.encode('data: [DONE]\n\n'),
      ]),
      200,
      headers: {'content-type': 'text/event-stream'},
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

  test('non-streaming chat uses selected model and does not log API key in body', () async {
    final httpClient = CapturingHttpClient(
      responseBody: {
        'choices': [
          {
            'message': {'content': 'ok'},
          },
        ],
      },
    );
    final client = LlmStudioClient('http://127.0.0.1:8000', httpClient: httpClient)
      ..userId = 'admin'
      ..apiKey = 'sk-test-key';

    await client.chat('model-selected', [
      {'role': 'user', 'content': 'hello'},
    ]);

    final request = httpClient.requests.single;
    final body = jsonDecode(request.body) as Map<String, dynamic>;
    expect(body['model'], 'model-selected');
    expect(body['model'], isNot('auto'));
    expect(request.body.contains('sk-test-key'), isFalse);
    expect(request.headers['Authorization'], 'Bearer sk-test-key');
  });

  test('streaming chat uses selected model', () async {
    final sseHttpClient = CapturingSseHttpClient();
    final client = LlmStudioClient(
      'http://127.0.0.1:8000',
      sseClient: SseClient(client: sseHttpClient),
    )..apiKey = 'sk-test-key';

    final tokens = await client.chatStream('model-stream', [
      {'role': 'user', 'content': 'hello'},
    ]).toList();

    final request = sseHttpClient.requests.single;
    final body = jsonDecode(request.body) as Map<String, dynamic>;
    expect(tokens, ['ok']);
    expect(body['model'], 'model-stream');
    expect(body['stream'], isTrue);
    expect(body['model'], isNot('auto'));
  });

  test('RAG query uses question payload and default top_k', () async {
    final httpClient = CapturingHttpClient();
    final client = LlmStudioClient('http://127.0.0.1:8000', httpClient: httpClient);

    await client.ragQuery('hello');

    final request = httpClient.requests.single;
    expect(request.url.path, '/v1/rag/query');
    final body = jsonDecode(request.body) as Map<String, dynamic>;
    expect(body['question'], 'hello');
    expect(body['top_k'], 5);
    expect(body.containsKey('query'), isFalse);
  });

  test('Adapter actions include model body when model context is available', () async {
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

  test('Adapter deactivate and unload send empty JSON object without model context', () async {
    final httpClient = CapturingHttpClient();
    final client = LlmStudioClient('http://127.0.0.1:8000', httpClient: httpClient);

    await client.deactivateAdapter('adapter-1');
    await client.unloadAdapter('adapter-1');

    expect(jsonDecode(httpClient.requests[0].body), <String, dynamic>{});
    expect(jsonDecode(httpClient.requests[1].body), <String, dynamic>{});
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

  test('known backend error codes map to AppError messages', () {
    expect(mapApiErrorMessage('ADAPTER_MODEL_REQUIRED', 'fallback'), contains('基础模型'));
    expect(mapApiErrorMessage('MODEL_DELETE_CONFIRM_REQUIRED', 'fallback'), contains('确认'));
    expect(mapApiErrorMessage('RAG_PATH_NOT_ALLOWED', 'fallback'), contains('路径'));
    expect(mapApiErrorMessage('VISION_PATH_NOT_ALLOWED', 'fallback'), contains('图片'));
    expect(mapApiErrorMessage('GPU_BUSY', 'fallback'), contains('GPU'));
  });

  test('403 is converted to PermissionDeniedException', () async {
    final httpClient = CapturingHttpClient(
      statusCode: 403,
      responseBody: {
        'error': {
          'code': 'PERMISSION_DENIED',
          'message': 'denied',
        },
      },
    );
    final client = LlmStudioClient('http://127.0.0.1:8000', httpClient: httpClient);

    expect(client.runtime, throwsA(isA<PermissionDeniedException>()));
  });

  test('GPU_BUSY and path errors are converted to StudioApiException', () async {
    for (final code in ['GPU_BUSY', 'RAG_PATH_NOT_ALLOWED', 'VISION_PATH_NOT_ALLOWED']) {
      final httpClient = CapturingHttpClient(
        statusCode: 409,
        responseBody: {
          'error': {
            'code': code,
            'message': 'backend message',
          },
        },
      );
      final client = LlmStudioClient('http://127.0.0.1:8000', httpClient: httpClient);

      await expectLater(
        client.runtime(),
        throwsA(
          isA<StudioApiException>().having((error) => error.code, 'code', code),
        ),
      );
    }
  });
}
