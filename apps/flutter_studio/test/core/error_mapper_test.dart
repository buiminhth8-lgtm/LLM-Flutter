import 'package:flutter_studio/core/errors/error_mapper.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('error mapper presents GPU busy in Chinese', () {
    final message = mapApiErrorMessage('GPU_BUSY', 'busy');

    expect(message, contains('GPU'));
    expect(message, isNot('busy'));
  });

  test('error mapper covers path and diagnostics errors', () {
    expect(mapApiErrorMessage('RAG_PATH_NOT_ALLOWED', ''), contains('路径'));
    expect(mapApiErrorMessage('VISION_PATH_NOT_ALLOWED', ''), contains('图片'));
    expect(mapApiErrorMessage('DIAGNOSTICS_EXPORT_FAILED', ''), contains('诊断包'));
  });

  test('error mapper avoids empty unknown fallback', () {
    expect(mapApiErrorMessage('NEW_CODE', ''), contains('后端日志'));
  });

  test('error mapper preserves unknown fallback', () {
    expect(mapApiErrorMessage('NEW_CODE', 'fallback'), 'fallback');
  });
}
