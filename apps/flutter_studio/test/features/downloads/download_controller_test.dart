import 'dart:convert';

import 'package:flutter_studio/core/api/api_client.dart';
import 'package:flutter_studio/features/downloads/download_controller.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

class SequenceDownloadClient extends http.BaseClient {
  int downloadsCalls = 0;

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    final path = request.url.path;
    Object payload = {'status': 'ok'};
    if (path == '/v1/downloads') {
      downloadsCalls += 1;
      payload = {
        'data': [
          {
            'job_id': 'job-a',
            'repo_id': 'org/model',
            'status': downloadsCalls == 1 ? 'running' : 'succeeded',
            'percent': downloadsCalls == 1 ? 50.0 : 100.0,
            'model_id': downloadsCalls == 1 ? null : 'model-a',
            'can_cancel': downloadsCalls == 1,
            'can_retry': false,
          },
        ],
      };
    }
    return http.StreamedResponse(
      Stream.value(utf8.encode(jsonEncode(payload))),
      200,
      headers: {'content-type': 'application/json'},
    );
  }
}

void main() {
  test('DownloadController refreshes running then completed task', () async {
    final httpClient = SequenceDownloadClient();
    final controller = DownloadController(
      LlmStudioClient('http://127.0.0.1:8000', httpClient: httpClient),
    );

    await controller.refresh();
    expect(controller.state.downloads.single.status, 'running');
    expect(controller.state.downloads.single.percent, 50.0);

    await controller.refresh();
    expect(controller.state.downloads.single.status, 'succeeded');
    expect(controller.state.downloads.single.modelId, 'model-a');

    controller.dispose();
  });
}

