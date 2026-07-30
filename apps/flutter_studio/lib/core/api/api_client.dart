import 'dart:convert';

import 'package:http/http.dart' as http;

import '../errors/error_mapper.dart';
import '../logging/client_logger.dart';
import '../models/dto.dart';
import 'api_exception.dart';
import 'sse_client.dart';

class LlmStudioClient {
  LlmStudioClient(this.baseUrl, {http.Client? httpClient, this._sseClient})
    : _httpClient = httpClient ?? http.Client();

  String baseUrl;
  String userId = 'admin';
  String apiKey = '';
  final http.Client _httpClient;
  final SseClient? _sseClient;

  Future<Map<String, dynamic>> health() async =>
      _getMap('/health', authenticated: false);

  Future<Map<String, dynamic>> setupStatus() async =>
      _getMap('/v1/setup/status', authenticated: false);

  Future<Map<String, dynamic>> initialize({
    required String adminPassword,
  }) async {
    return _postMap(
      '/v1/setup/initialize',
      authenticated: false,
      body: {'admin_password': adminPassword, 'display_name': 'Admin'},
      timeout: const Duration(seconds: 15),
    );
  }

  Future<Map<String, dynamic>> runtime() async => _getMap('/v1/runtime');

  Future<List<dynamic>> capabilities() async {
    final body = await _getMap('/v1/capabilities');
    return (body['capabilities'] as List?) ?? const [];
  }

  Future<AuthUserDto> currentAuthUser() async {
    final body = await _getMap('/v1/auth/me');
    final user = body['user'];
    if (user is Map) {
      return AuthUserDto.fromMap(user);
    }
    throw StudioApiException('API response does not contain current user.');
  }

  Future<List<AuthUserDto>> authUsers() async {
    final body = await _getMap('/v1/auth/users');
    final users = (body['users'] as List?) ?? const [];
    return users
        .whereType<Map>()
        .map((item) => AuthUserDto.fromMap(item))
        .toList();
  }

  Future<RegeneratedApiKeyDto> regenerateApiKey(String userId) async {
    final body = await _postMap(
      '/v1/auth/users/${Uri.encodeComponent(userId)}/regenerate',
      body: const {},
    );
    return RegeneratedApiKeyDto.fromMap(body);
  }

  Future<List<dynamic>> models() async {
    final body = await _getMap('/v1/models');
    return (body['data'] as List?) ?? const [];
  }

  Future<void> scanModels() async {
    await _postMap('/v1/models/scan', timeout: const Duration(seconds: 15));
  }

  Future<Map<String, dynamic>> loadModel(String modelId) async {
    return _postMap(
      '/v1/models/${Uri.encodeComponent(modelId)}/load',
      body: {'strategy': 'auto'},
      timeout: const Duration(minutes: 10),
    );
  }

  Future<void> unloadModel(String modelId) async {
    await _postMap(
      '/v1/models/unload',
      body: {'model': modelId},
      timeout: const Duration(seconds: 30),
    );
  }

  Future<Map<String, dynamic>> currentModel() async =>
      _getMap('/v1/models/current');

  Future<Map<String, dynamic>> gpuScheduler() async =>
      _getMap('/v1/gpu/scheduler');

  Future<List<dynamic>> jobs({int limit = 20}) async {
    final body = await _getMap('/v1/jobs?limit=$limit');
    return (body['data'] as List?) ?? const [];
  }

  Future<List<DownloadTaskDto>> downloads() async {
    final body = await _getMap('/v1/downloads');
    final items = (body['data'] as List?) ?? const [];
    return items
        .whereType<Map>()
        .map((item) => DownloadTaskDto.fromMap(item))
        .toList();
  }

  Future<Map<String, dynamic>> startDownload({
    required String repoId,
    String provider = 'modelscope',
    String? revision,
    List<String>? allowPatterns,
    List<String>? ignorePatterns,
  }) {
    return _postMap(
      '/v1/downloads',
      body: {
        'provider': provider,
        'repo_id': repoId,
        if (revision != null && revision.isNotEmpty) 'revision': revision,
        if (allowPatterns != null && allowPatterns.isNotEmpty)
          'allow_patterns': allowPatterns,
        if (ignorePatterns != null && ignorePatterns.isNotEmpty)
          'ignore_patterns': ignorePatterns,
      },
    );
  }

  Future<void> cancelDownload(String id) async =>
      _postMap('/v1/downloads/${Uri.encodeComponent(id)}/cancel');

  Future<void> retryDownload(String id) async =>
      _postMap('/v1/downloads/${Uri.encodeComponent(id)}/retry');

  Future<void> deleteDownloadRecord(String id) async {
    final response = await _httpClient
        .delete(
          Uri.parse('$baseUrl/v1/downloads/${Uri.encodeComponent(id)}'),
          headers: _authHeaders(),
        )
        .timeout(const Duration(seconds: 30));
    _decodeMap(response);
  }

  Future<List<dynamic>> adapters() async {
    final body = await _getMap('/v1/adapters');
    return (body['data'] as List?) ?? (body['adapters'] as List?) ?? const [];
  }

  Future<void> scanAdapters() async => _postMap('/v1/adapters/scan');

  Future<void> loadAdapter(String id, String modelId) async => _postMap(
    '/v1/adapters/${Uri.encodeComponent(id)}/load',
    body: {'model': modelId},
  );

  Future<void> activateAdapter(String id, String modelId) async => _postMap(
    '/v1/adapters/${Uri.encodeComponent(id)}/activate',
    body: {'model': modelId},
  );

  Future<void> deactivateAdapter(String id, {String? modelId}) async =>
      _postMap(
        '/v1/adapters/${Uri.encodeComponent(id)}/deactivate',
        body: modelId == null || modelId.isEmpty
            ? const {}
            : {'model': modelId},
      );

  Future<void> unloadAdapter(String id, {String? modelId}) async => _postMap(
    '/v1/adapters/${Uri.encodeComponent(id)}/unload',
    body: modelId == null || modelId.isEmpty ? const {} : {'model': modelId},
  );

  Future<List<dynamic>> benchmarks() async {
    final body = await _getMap('/v1/benchmarks');
    return (body['data'] as List?) ?? const [];
  }

  Future<Map<String, dynamic>> startBenchmark({
    required String modelId,
    int maxNewTokens = 128,
    int contextLength = 512,
  }) {
    return _postMap(
      '/v1/benchmarks',
      body: {
        'model_id': modelId,
        'prompt_set': 'default',
        'warmup_runs': 1,
        'measured_runs': 3,
        'max_new_tokens': maxNewTokens,
        'context_lengths': [contextLength],
        'seed': 42,
      },
    );
  }

  Future<Map<String, dynamic>> storage() async => _getMap('/v1/storage');

  Future<Map<String, dynamic>> cleanupPreview() async =>
      _postMap('/v1/storage/cleanup/preview');

  Future<Map<String, dynamic>> cleanupStorage() async =>
      _postMap('/v1/storage/cleanup');

  Future<Map<String, dynamic>> exportDiagnostics() async =>
      _postMap('/v1/diagnostics/export');

  Future<String> ragQuery(String query, {int topK = 5}) async {
    final body = await _postMap(
      '/v1/rag/query',
      body: {'question': query, 'top_k': topK},
    );
    return jsonEncode(body);
  }

  Future<String> chat(
    String modelId,
    List<Map<String, String>> messages,
  ) async {
    final body = await _postMap(
      '/v1/chat/completions',
      body: {'model': modelId, 'messages': messages, 'stream': false},
      timeout: const Duration(minutes: 5),
    );
    final choices = body['choices'];
    if (choices is List && choices.isNotEmpty) {
      final message = choices.first['message'];
      if (message is Map && message['content'] is String) {
        return message['content'] as String;
      }
    }
    return jsonEncode(body);
  }

  Stream<String> chatStream(
    String modelId,
    List<Map<String, String>> messages,
  ) {
    final sse = _sseClient ?? SseClient();
    return sse.postJsonTokens(
      uri: Uri.parse('$baseUrl/v1/chat/completions'),
      headers: _authHeaders(),
      body: {'model': modelId, 'messages': messages, 'stream': true},
    );
  }

  Future<void> cancelJob(String id) async =>
      _postMap('/v1/jobs/${Uri.encodeComponent(id)}/cancel');

  Future<Map<String, dynamic>> registerExternalModel(String path) async {
    return _postMap('/v1/models/register', body: {'path': path});
  }

  Future<void> deleteModel(String modelId, {required bool confirm}) async {
    final uri = Uri.parse(
      '$baseUrl/v1/models/${Uri.encodeComponent(modelId)}',
    ).replace(queryParameters: {'confirm': confirm ? 'true' : 'false'});
    final response = await _httpClient
        .delete(uri, headers: _authHeaders())
        .timeout(const Duration(seconds: 30));
    _decodeMap(response);
  }

  Map<String, String> authHeadersForTesting() => _authHeaders();

  Future<Map<String, dynamic>> _getMap(
    String path, {
    bool authenticated = true,
  }) async {
    final response = await _httpClient
        .get(
          Uri.parse('$baseUrl$path'),
          headers: authenticated ? _authHeaders() : const {},
        )
        .timeout(const Duration(seconds: 8));
    return _decodeMap(response);
  }

  Future<Map<String, dynamic>> _postMap(
    String path, {
    Map<String, Object?>? body,
    bool authenticated = true,
    Duration timeout = const Duration(seconds: 30),
  }) async {
    final response = await _httpClient
        .post(
          Uri.parse('$baseUrl$path'),
          headers: {
            if (authenticated) ..._authHeaders(),
            'content-type': 'application/json',
          },
          body: body == null ? null : jsonEncode(body),
        )
        .timeout(timeout);
    return _decodeMap(response);
  }

  Map<String, dynamic> _decodeMap(http.Response response) {
    final dynamic body = response.body.isEmpty
        ? <String, dynamic>{}
        : jsonDecode(response.body);
    if (response.statusCode >= 400) {
      if (body is Map && body['error'] is Map) {
        final error = body['error'] as Map;
        final code = '${error['code']}';
        final message = '${error['message']}';
        logClientError('API ${response.statusCode} $code: $message');
        throw exceptionForApiError(
          statusCode: response.statusCode,
          code: code,
          message: message,
        );
      }
      logClientError('HTTP ${response.statusCode}: ${response.body}');
      throw StudioApiException(
        'HTTP ${response.statusCode}: ${response.body}',
        statusCode: response.statusCode,
      );
    }
    if (body is Map<String, dynamic>) {
      return body;
    }
    throw StudioApiException('API response is not a JSON object.');
  }

  Map<String, String> _authHeaders() {
    if (apiKey.isEmpty) {
      return const {};
    }
    final trimmedUserId = userId.trim();
    if (trimmedUserId.isEmpty) {
      return {'Authorization': 'Bearer $apiKey'};
    }
    return {
      'X-User-ID': trimmedUserId,
      'X-API-Key': apiKey,
      'Authorization': 'Bearer $apiKey',
    };
  }
}
