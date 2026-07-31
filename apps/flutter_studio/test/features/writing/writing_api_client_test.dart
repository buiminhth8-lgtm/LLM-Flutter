import 'dart:convert';

import 'package:flutter_studio/core/api/api_client.dart';
import 'package:flutter_studio/core/api/sse_client.dart';
import 'package:flutter_studio/features/writing/models/target_length_dto.dart';
import 'package:flutter_studio/features/writing/models/writing_generation_request_dto.dart';
import 'package:flutter_studio/features/writing/writing_api_client.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

class WritingContractHttpClient extends http.BaseClient {
  final List<http.BaseRequest> requests = [];

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    requests.add(request);
    final path = request.url.path;
    if (path == '/v1/writing/stream') {
      final payload = [
        'data: {"type":"start","generation_id":"gen-stream"}\n\n',
        'data: {"type":"delta","text":"夜色"}\n\n',
        'data: {"type":"done","generation_id":"gen-stream","finish_reason":"stop"}\n\n',
      ].join();
      return http.StreamedResponse(
        Stream.value(utf8.encode(payload)),
        200,
        headers: {'content-type': 'text/event-stream'},
      );
    }
    Object body;
    if (path == '/v1/writing/generate') {
      body = _result('gen-1');
    } else if (path == '/v1/writing/generations') {
      body = {
        'data': [_record('gen-1')],
      };
    } else if (path == '/v1/writing/generations/gen-1' &&
        request.method == 'GET') {
      body = _record('gen-1');
    } else {
      body = {'status': 'ok'};
    }
    return http.StreamedResponse(
      Stream.value(utf8.encode(jsonEncode(body))),
      200,
      headers: {'content-type': 'application/json'},
    );
  }

  static Map<String, Object?> _result(String id) => {
    'generation_id': id,
    'project_id': 'p1',
    'chapter_id': 'c1',
    'mode': 'chapter_generate',
    'model_id': 'm1',
    'adapter_id': null,
    'text': '夜色沉入旧城。',
    'finish_reason': 'stop',
    'output_char_count': 7,
    'input_token_estimate': 20,
    'output_token_estimate': 8,
    'warnings': <Object?>[],
  };

  static Map<String, Object?> _record(String id) => {
    ..._result(id),
    'prompt_rendered': '生成章节',
    'model_output': '夜色沉入旧城。',
    'input_context': <String, Object?>{},
    'generation_params': {'temperature': 0.8},
    'target_length': {'unit': 'chars', 'min': 1, 'max': 100},
    'status': 'succeeded',
    'created_at': '2026-07-30T10:00:00Z',
    'updated_at': '2026-07-30T10:00:01Z',
  };
}

void main() {
  test(
    'Writing API parses generation result, record, list, and stream',
    () async {
      final httpClient = WritingContractHttpClient();
      final rawClient = LlmStudioClient(
        'http://127.0.0.1:8000',
        httpClient: httpClient,
        sseClient: SseClient(client: httpClient),
      );
      final api = WritingApiClient(rawClient);
      const request = WritingGenerationRequestDto(
        projectId: 'p1',
        chapterId: 'c1',
        templateId: 't1',
        modelId: 'm1',
        targetLength: TargetLengthDto(min: 1, max: 100),
      );

      final result = await api.generateWriting(request);
      final record = await api.getGeneration(result.generationId);
      final listed = await api.listGenerations(
        projectId: 'p1',
        chapterId: 'c1',
      );
      final events = await api.streamWriting(request).toList();
      await api.saveGenerationToChapter(result.generationId);
      await api.cancelGeneration(result.generationId);

      expect(result.text, '夜色沉入旧城。');
      expect(record.modelOutput, result.text);
      expect(record.targetLength['unit'], 'chars');
      expect(listed.single.generationId, 'gen-1');
      expect(events.map((item) => item.type), ['start', 'delta', 'done']);
      expect(events[1].text, '夜色');
      expect(
        httpClient.requests.any(
          (request) =>
              request.url.path.endsWith('/save-to-chapter') &&
              request.method == 'POST',
        ),
        isTrue,
      );
    },
  );
}
