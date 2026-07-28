import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

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
      throw StudioApiException('HTTP ${response.statusCode}: $text', statusCode: response.statusCode);
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

  void close() => _client.close();
}
