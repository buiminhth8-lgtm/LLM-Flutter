import 'package:flutter_studio/core/backend/backend_service_io.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('backend service launches the pure Python service module', () {
    final args = buildBackendServiceArgumentsForTesting(
      host: '127.0.0.1',
      port: '8000',
    );

    expect(args, containsAllInOrder(['-m', 'llm_studio.server']));
    expect(args, isNot(contains('llm-studio.exe')));
    expect(args, isNot(contains('llm_studio.cli')));
  });

  test('backend service preserves python launcher prefix', () {
    final args = buildBackendServiceArgumentsForTesting(
      host: '127.0.0.1',
      port: '8000',
      pythonPrefix: const ['-3.12'],
    );

    expect(args.first, '-3.12');
    expect(args, containsAllInOrder(['-m', 'llm_studio.server']));
  });

  test('backend log redaction hides secrets', () {
    final redacted = redactBackendLogForTesting(
      'Authorization: Bearer sk-secret api_key=abc password=hunter2 cookie=session token=raw',
    );

    expect(redacted, isNot(contains('sk-secret')));
    expect(redacted, isNot(contains('hunter2')));
    expect(redacted, contains('<redacted>'));
  });
}
