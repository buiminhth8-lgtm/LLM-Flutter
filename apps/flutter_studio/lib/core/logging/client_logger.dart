import 'package:flutter/foundation.dart';

typedef ClientLogSink = void Function(String message);

ClientLogSink _sink = debugPrint;

void setClientLogSinkForTesting(ClientLogSink sink) {
  _sink = sink;
}

void resetClientLogSinkForTesting() {
  _sink = debugPrint;
}

void logClientInfo(String message) {
  _emit('INFO', message);
}

void logClientError(Object error, [StackTrace? stackTrace]) {
  final stack = stackTrace == null ? '' : '\n${_redact(stackTrace.toString())}';
  _emit('ERROR', '${_redact(error.toString())}$stack');
}

String redactClientLogForTesting(String value) => _redact(value);

void _emit(String level, String message) {
  _sink('[LLM-Studio Flutter][$level] ${_redact(message)}');
}

String _redact(String value) {
  var redacted = value.replaceAll(
    RegExp(r'Authorization:\s*Bearer\s+\S+', caseSensitive: false),
    'Authorization: Bearer <redacted>',
  );
  redacted = redacted.replaceAll(
    RegExp(r'X-API-Key:\s*\S+', caseSensitive: false),
    'X-API-Key: <redacted>',
  );
  redacted = redacted.replaceAllMapped(
    RegExp(
      r'(api_key|access_token|password|cookie|token)=\S+',
      caseSensitive: false,
    ),
    (match) => '${match.group(1)}=<redacted>',
  );
  return redacted;
}
