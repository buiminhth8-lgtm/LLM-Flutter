import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import '../errors/error_mapper.dart';
import 'api_exception.dart';

class SseClient {
  SseClient({http.Client? client}) : _client = client ?? http.Client();

  final http.Client _client;

  Stream<String> postJsonTokens({
    required Uri uri,
    required Map<String, String> headers,
    required Map<String, Object?> body,
  }) async* {
    final request = http.Request('POST', uri)
      ..headers.addAll(headers)
      ..headers['content-type'] = 'application/json'
      ..body = jsonEncode(body);
    final response = await _client.send(request);
    if (response.statusCode >= 400) {
      final text = await response.stream.bytesToString();
      throw StudioApiException(
        'HTTP ${response.statusCode}: $text',
        statusCode: response.statusCode,
      );
    }

    final lines = response.stream
        .transform(utf8.decoder)
        .transform(const LineSplitter());
    await for (final line in lines) {
      final token = parseSseLine(line);
      if (token == null) {
        continue;
      }
      if (token == '[DONE]') {
        break;
      }
      yield token;
    }
  }

  Stream<Map<String, dynamic>> postJsonEvents({
    required Uri uri,
    required Map<String, String> headers,
    required Map<String, Object?> body,
  }) async* {
    final request = http.Request('POST', uri)
      ..headers.addAll(headers)
      ..headers['content-type'] = 'application/json'
      ..body = jsonEncode(body);
    final response = await _client.send(request);
    if (response.statusCode >= 400) {
      final text = await response.stream.bytesToString();
      try {
        final decoded = jsonDecode(text);
        if (decoded is Map && decoded['error'] is Map) {
          final error = decoded['error'] as Map;
          throw exceptionForApiError(
            statusCode: response.statusCode,
            code: '${error['code'] ?? 'HTTP_ERROR'}',
            message: '${error['message'] ?? text}',
          );
        }
      } on StudioApiException {
        rethrow;
      } on FormatException {
        // Fall through to a generic HTTP error.
      }
      throw StudioApiException(
        'HTTP ${response.statusCode}: $text',
        statusCode: response.statusCode,
      );
    }

    final lines = response.stream
        .transform(utf8.decoder)
        .transform(const LineSplitter());
    await for (final line in lines) {
      final event = parseSseEvent(line);
      if (event != null) {
        yield event;
      }
    }
  }

  static String? parseSseLine(String line) {
    if (!line.startsWith('data:')) {
      return null;
    }
    final payload = line.substring(5).trimLeft();
    if (payload == '[DONE]') {
      return '[DONE]';
    }
    final decoded = jsonDecode(payload);
    if (decoded is Map) {
      final choices = decoded['choices'];
      if (choices is List && choices.isNotEmpty) {
        final first = choices.first;
        if (first is Map) {
          final delta = first['delta'];
          if (delta is Map && delta['content'] is String) {
            return delta['content'] as String;
          }
        }
      }
    }
    return null;
  }

  static Map<String, dynamic>? parseSseEvent(String line) {
    if (!line.startsWith('data:')) {
      return null;
    }
    final payload = line.substring(5).trimLeft();
    if (payload.isEmpty || payload == '[DONE]') {
      return null;
    }
    final decoded = jsonDecode(payload);
    if (decoded is! Map) {
      return null;
    }
    return decoded.map((key, value) => MapEntry('$key', value));
  }

  void close() => _client.close();
}
