import 'dart:convert';

import 'package:flutter_studio/core/api/api_client.dart';
import 'package:flutter_studio/features/settings/model_profiles/model_profiles_api_client.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

class _ModelProfilesHttpClient extends http.BaseClient {
  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    Object body;
    if (request.url.path == '/v1/model-profiles') {
      body = {
        'data': [
          {
            'id': 'p1',
            'name': 'Local Runtime Default',
            'provider': 'local_runtime',
            'model': null,
            'status': 'enabled',
            'default_params': {'temperature': 0.8},
            'capabilities': {'stream': true},
            'connection': {},
            'metadata': {'builtin': true},
            'is_default': true,
          },
        ],
      };
    } else if (request.url.path == '/v1/model-profiles/defaults/ensure') {
      body = {'created': 2, 'skipped': 0};
    } else {
      body = {'data': <Object?>[]};
    }
    return http.StreamedResponse(
      Stream.value(utf8.encode(jsonEncode(body))),
      200,
      headers: {'content-type': 'application/json'},
    );
  }
}

void main() {
  test('ModelProfilesApiClient lists and parses profiles', () async {
    final api = ModelProfilesApiClient(
      LlmStudioClient(
        'http://127.0.0.1:8000',
        httpClient: _ModelProfilesHttpClient(),
      ),
    );

    final profiles = await api.listProfiles();

    expect(profiles, hasLength(1));
    expect(profiles.single.name, 'Local Runtime Default');
    expect(profiles.single.provider, 'local_runtime');
    expect(profiles.single.isDefault, isTrue);
    expect(profiles.single.isBuiltin, isTrue);
    expect(profiles.single.defaultParams['temperature'], 0.8);
  });

  test('ModelProfilesApiClient parses ensure defaults summary', () async {
    final api = ModelProfilesApiClient(
      LlmStudioClient(
        'http://127.0.0.1:8000',
        httpClient: _ModelProfilesHttpClient(),
      ),
    );

    final summary = await api.ensureDefaults();

    expect(summary['created'], 2);
    expect(summary['skipped'], 0);
  });
}
