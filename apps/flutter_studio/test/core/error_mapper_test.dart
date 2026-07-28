import 'package:flutter_studio/core/errors/error_mapper.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('error mapper presents GPU busy in Chinese', () {
    final message = mapApiErrorMessage('GPU_BUSY', 'busy');

    expect(message, contains('GPU'));
    expect(message, isNot('busy'));
  });

  test('error mapper preserves unknown fallback', () {
    expect(mapApiErrorMessage('NEW_CODE', 'fallback'), 'fallback');
  });
}
