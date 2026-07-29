import 'package:flutter_studio/core/logging/client_logger.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  tearDown(resetClientLogSinkForTesting);

  test('client logger writes redacted errors to console sink', () {
    final lines = <String>[];
    setClientLogSinkForTesting(lines.add);

    logClientError(
      'failed Authorization: Bearer sk-secret api_key=abc password=hunter2 cookie=session token=raw',
    );

    expect(lines.single, contains('[LLM-Studio Flutter][ERROR]'));
    expect(lines.single, contains('Authorization: Bearer <redacted>'));
    expect(lines.single, contains('api_key=<redacted>'));
    expect(lines.single, contains('password=<redacted>'));
    expect(lines.single, contains('cookie=<redacted>'));
    expect(lines.single, contains('token=<redacted>'));
    expect(lines.single, isNot(contains('sk-secret')));
    expect(lines.single, isNot(contains('hunter2')));
  });
}
