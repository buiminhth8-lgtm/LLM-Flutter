import 'dart:convert';

import 'package:flutter_studio/core/api/api_client.dart';
import 'package:flutter_studio/core/errors/error_mapper.dart';
import 'package:flutter_studio/core/models/dto.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

class CapturedDownloadRequest {
  CapturedDownloadRequest(this.method, this.url, this.body);

  final String method;
  final Uri url;
  final String body;
}

class DownloadHttpClient extends http.BaseClient {
  DownloadHttpClient({this.responseBody = const {'status': 'ok'}});

  final Map<String, Object?> responseBody;
  final requests = <CapturedDownloadRequest>[];

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    final body = request is http.Request ? request.body : '';
    requests.add(CapturedDownloadRequest(request.method, request.url, body));
    return http.StreamedResponse(
      Stream.value(utf8.encode(jsonEncode(responseBody))),
      200,
      headers: {'content-type': 'application/json'},
    );
  }
}

void main() {
  test(
    'startDownload body supports provider revision and pattern filters',
    () async {
      final httpClient = DownloadHttpClient();
      final client = LlmStudioClient(
        'http://127.0.0.1:8000',
        httpClient: httpClient,
      );

      await client.startDownload(
        provider: 'modelscope',
        repoId: 'org/model',
        revision: 'main',
        allowPatterns: ['*.json'],
        ignorePatterns: ['*.md'],
      );

      final request = httpClient.requests.single;
      final body = jsonDecode(request.body) as Map<String, dynamic>;
      expect(request.url.path, '/v1/downloads');
      expect(body['provider'], 'modelscope');
      expect(body['repo_id'], 'org/model');
      expect(body['revision'], 'main');
      expect(body['allow_patterns'], ['*.json']);
      expect(body['ignore_patterns'], ['*.md']);
    },
  );

  test(
    'downloads parse provider null total bytes and nullable percent',
    () async {
      final httpClient = DownloadHttpClient(
        responseBody: {
          'data': [
            {
              'job_id': 'job-a',
              'provider': 'modelscope',
              'repo_id': 'org/model',
              'status': 'running',
              'downloaded_bytes': 128,
              'total_bytes': null,
              'percent': null,
              'can_cancel': true,
              'can_retry': false,
            },
          ],
        },
      );
      final client = LlmStudioClient(
        'http://127.0.0.1:8000',
        httpClient: httpClient,
      );

      final downloads = await client.downloads();

      expect(downloads.single, isA<DownloadTaskDto>());
      expect(downloads.single.provider, 'modelscope');
      expect(downloads.single.totalBytes, isNull);
      expect(downloads.single.percent, isNull);
      expect(downloads.single.canCancel, isTrue);
    },
  );

  test('downloads infer actions for legacy records without can_* fields', () {
    final running = DownloadTaskDto.fromMap({
      'job_id': 'running',
      'status': 'running',
    });
    final failed = DownloadTaskDto.fromMap({
      'job_id': 'failed',
      'status': 'failed',
    });

    expect(running.canCancel, isTrue);
    expect(running.canDelete, isFalse);
    expect(failed.canCancel, isFalse);
    expect(failed.canRetry, isTrue);
    expect(failed.canDelete, isTrue);
  });

  test('cancel retry and delete use stable endpoints', () async {
    final httpClient = DownloadHttpClient();
    final client = LlmStudioClient(
      'http://127.0.0.1:8000',
      httpClient: httpClient,
    );

    await client.cancelDownload('job-a');
    await client.retryDownload('job-b');
    await client.deleteDownloadRecord('job-c');

    expect(httpClient.requests[0].url.path, '/v1/downloads/job-a/cancel');
    expect(httpClient.requests[1].url.path, '/v1/downloads/job-b/retry');
    expect(httpClient.requests[2].method, 'DELETE');
    expect(httpClient.requests[2].url.path, '/v1/downloads/job-c');
  });

  test('download error codes map to Chinese messages', () {
    expect(mapApiErrorMessage('DOWNLOAD_DISK_FULL', ''), contains('磁盘空间不足'));
    expect(mapApiErrorMessage('DOWNLOAD_NETWORK_ERROR', ''), contains('网络错误'));
    expect(
      mapApiErrorMessage('DOWNLOAD_MODEL_SCAN_FAILED', ''),
      contains('模型扫描注册失败'),
    );
    expect(
      mapApiErrorMessage('MODELSCOPE_DOWNLOAD_FAILED', ''),
      contains('魔塔模型下载失败'),
    );
  });
}
