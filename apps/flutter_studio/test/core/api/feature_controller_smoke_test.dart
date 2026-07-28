import 'dart:convert';

import 'package:flutter_studio/core/api/api_client.dart';
import 'package:flutter_studio/features/adapters/adapter_controller.dart';
import 'package:flutter_studio/features/diagnostics/diagnostics_controller.dart';
import 'package:flutter_studio/features/jobs/job_controller.dart';
import 'package:flutter_studio/features/models/model_controller.dart';
import 'package:flutter_studio/features/rag/rag_controller.dart';
import 'package:flutter_studio/features/storage/storage_controller.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

class CapturedControllerRequest {
  CapturedControllerRequest(this.method, this.path, this.body);

  final String method;
  final String path;
  final String body;
}

class RoutingHttpClient extends http.BaseClient {
  final requests = <CapturedControllerRequest>[];

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    final body = request is http.Request ? request.body : '';
    requests.add(CapturedControllerRequest(request.method, request.url.path, body));
    final payload = _payloadFor(request.method, request.url.path);
    return http.StreamedResponse(
      Stream.value(utf8.encode(jsonEncode(payload))),
      200,
      headers: {'content-type': 'application/json'},
    );
  }

  Map<String, Object?> _payloadFor(String method, String path) {
    if (path == '/v1/models') {
      return {
        'data': [
          {'id': 'model-a', 'status': 'ready'},
        ],
      };
    }
    if (path == '/v1/models/current') {
      return {'loaded': true, 'model_id': 'model-a'};
    }
    if (path == '/v1/models/model-a/load') {
      return {'model_id': 'model-a', 'status': 'loaded'};
    }
    if (path == '/v1/jobs') {
      return {
        'data': [
          {'id': 'job-a', 'status': 'succeeded'},
        ],
      };
    }
    if (path == '/v1/adapters') {
      return {
        'data': [
          {'id': 'adapter-a', 'compatible': true},
        ],
      };
    }
    if (path == '/v1/rag/query') {
      return {'answer': 'rag answer'};
    }
    if (path == '/v1/storage') {
      return {'categories': []};
    }
    if (path == '/v1/storage/cleanup/preview') {
      return {'items': []};
    }
    if (path == '/v1/diagnostics/export') {
      return {'path': r'C:\tmp\diagnostics.zip'};
    }
    return {'status': 'ok'};
  }
}

void main() {
  test('ModelController refreshes current model and deletes with confirm', () async {
    final httpClient = RoutingHttpClient();
    final controller = ModelController(
      LlmStudioClient('http://127.0.0.1:8000', httpClient: httpClient),
    );

    await controller.refresh();
    expect(controller.models.single['id'], 'model-a');
    expect(controller.activeModelId(), 'model-a');

    await controller.delete('model-a');
    final deleteRequest = httpClient.requests.firstWhere(
      (request) => request.method == 'DELETE',
    );
    expect(deleteRequest.path, '/v1/models/model-a');
  });

  test('RagController stores query result', () async {
    final controller = RagController(
      LlmStudioClient('http://127.0.0.1:8000', httpClient: RoutingHttpClient()),
    );

    controller.queryController.text = 'hello';
    await controller.query();

    expect(controller.state.result, contains('rag answer'));
    controller.dispose();
  });

  test('AdapterController sends model context and refreshes adapters', () async {
    final httpClient = RoutingHttpClient();
    final controller = AdapterController(
      LlmStudioClient('http://127.0.0.1:8000', httpClient: httpClient),
    );

    await controller.load('adapter-a', 'model-a');

    final loadRequest = httpClient.requests.firstWhere(
      (request) => request.path == '/v1/adapters/adapter-a/load',
    );
    expect(jsonDecode(loadRequest.body)['model'], 'model-a');
    expect(controller.state.adapters.single['id'], 'adapter-a');
  });

  test('JobController cancel refreshes jobs', () async {
    final controller = JobController(
      LlmStudioClient('http://127.0.0.1:8000', httpClient: RoutingHttpClient()),
    );

    await controller.cancel('job-a');

    expect(controller.state.jobs.single['id'], 'job-a');
  });

  test('Storage and Diagnostics controllers store API results', () async {
    final client = LlmStudioClient(
      'http://127.0.0.1:8000',
      httpClient: RoutingHttpClient(),
    );
    final storage = StorageController(client);
    final diagnostics = DiagnosticsController(client);

    await storage.refresh();
    await storage.previewCleanup();
    await diagnostics.export();

    expect(storage.state.storage?['categories'], isA<List>());
    expect(storage.state.cleanupPreview?['items'], isA<List>());
    expect(diagnostics.state.exportResult, contains('diagnostics.zip'));
  });
}
