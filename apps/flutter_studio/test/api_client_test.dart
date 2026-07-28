import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_studio/main.dart';

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
}
