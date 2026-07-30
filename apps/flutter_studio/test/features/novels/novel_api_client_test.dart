import 'dart:async';
import 'dart:convert';

import 'package:flutter_studio/core/api/api_client.dart';
import 'package:flutter_studio/features/novels/novel_api_client.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

class CapturedNovelRequest {
  CapturedNovelRequest(this.method, this.path, this.body);

  final String method;
  final String path;
  final String body;
}

class NovelHttpClient extends http.BaseClient {
  final requests = <CapturedNovelRequest>[];

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    final body = request is http.Request ? request.body : '';
    requests.add(CapturedNovelRequest(request.method, request.url.path, body));
    Object responseBody = <String, Object?>{};
    if (request.method == 'GET') {
      responseBody = {'data': <Object?>[]};
    }
    if (request.url.path == '/v1/novels/projects' && request.method == 'POST') {
      responseBody = {
        'id': 'project-1',
        'title': 'Novel',
        'slug': 'novel',
        'status': 'active',
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
  test('Novel API client uses stable project paths', () async {
    final httpClient = NovelHttpClient();
    final api = NovelApiClient(
      LlmStudioClient('http://127.0.0.1:8000', httpClient: httpClient),
    );

    await api.listProjects();
    await api.createProject(title: 'Novel', genre: 'fantasy');
    await api.deleteProject('project-1');

    expect(httpClient.requests[0].path, '/v1/novels/projects');
    expect(httpClient.requests[1].method, 'POST');
    expect(httpClient.requests[1].path, '/v1/novels/projects');
    final body = jsonDecode(httpClient.requests[1].body) as Map;
    expect(body['title'], 'Novel');
    expect(body['genre'], 'fantasy');
    expect(httpClient.requests[2].method, 'DELETE');
    expect(httpClient.requests[2].path, '/v1/novels/projects/project-1');
  });

  test('Novel API client uses child resource paths', () async {
    final httpClient = NovelHttpClient();
    final api = NovelApiClient(
      LlmStudioClient('http://127.0.0.1:8000', httpClient: httpClient),
    );

    await api.listChapters('p1');
    await api.createChapter('p1', title: 'Chapter 1');
    await api.listCharacters('p1');
    await api.createCharacter('p1', name: 'Alice');
    await api.listWorldEntries('p1');
    await api.createWorldEntry(
      'p1',
      category: 'location',
      title: 'City',
      content: 'A city.',
    );

    expect(httpClient.requests[0].path, '/v1/novels/projects/p1/chapters');
    expect(httpClient.requests[1].path, '/v1/novels/projects/p1/chapters');
    expect(httpClient.requests[2].path, '/v1/novels/projects/p1/characters');
    expect(httpClient.requests[3].path, '/v1/novels/projects/p1/characters');
    expect(httpClient.requests[4].path, '/v1/novels/projects/p1/world');
    expect(httpClient.requests[5].path, '/v1/novels/projects/p1/world');
  });
}
