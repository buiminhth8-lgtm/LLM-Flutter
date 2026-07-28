import 'package:flutter_studio/core/api/sse_client.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('SSE parser extracts streamed chat token content', () {
    final token = SseClient.parseSseLine(
      'data: {"choices":[{"delta":{"content":"hello"}}]}',
    );

    expect(token, 'hello');
  });

  test('SSE parser recognizes DONE sentinel', () {
    expect(SseClient.parseSseLine('data: [DONE]'), '[DONE]');
  });

  test('SSE parser ignores non-data lines', () {
    expect(SseClient.parseSseLine(': keep-alive'), isNull);
  });
}
