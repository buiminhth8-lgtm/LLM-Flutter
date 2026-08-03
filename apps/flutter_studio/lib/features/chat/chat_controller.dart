import 'dart:async';

import 'package:flutter/foundation.dart';

import '../../core/api/api_client.dart';
import '../../core/models/dto.dart';

class ChatController extends ChangeNotifier {
  ChatController(this.client);

  final LlmStudioClient client;
  final List<ChatTurn> turns = <ChatTurn>[];
  StreamSubscription<String>? _subscription;
  bool isGenerating = false;
  bool streamingEnabled = true;
  String? lastError;

  Future<void> send({
    required String modelId,
    required String systemPrompt,
    required String userText,
  }) async {
    if (userText.trim().isEmpty || isGenerating) {
      return;
    }
    lastError = null;
    final nextTurns = [...turns, ChatTurn.user(userText.trim())];
    turns
      ..clear()
      ..addAll(nextTurns)
      ..add(ChatTurn.assistant(''));
    isGenerating = true;
    notifyListeners();

    final messages = _buildMessages(systemPrompt, nextTurns);
    try {
      if (streamingEnabled) {
        await _stream(modelId, messages);
      } else {
        final text = await client.chat(modelId, messages);
        turns[turns.length - 1] = ChatTurn.assistant(text);
      }
    } catch (error) {
      lastError = error.toString();
      if (turns.isNotEmpty &&
          turns.last.role == 'assistant' &&
          turns.last.content.isEmpty) {
        turns.removeLast();
      }
      rethrow;
    } finally {
      isGenerating = false;
      notifyListeners();
    }
  }

  Future<void> regenerate({
    required String modelId,
    required String systemPrompt,
  }) async {
    if (turns.isEmpty || isGenerating) {
      return;
    }
    while (turns.isNotEmpty && turns.last.role == 'assistant') {
      turns.removeLast();
    }
    final lastUser = turns.lastWhere(
      (turn) => turn.role == 'user',
      orElse: () => const ChatTurn(role: 'user', content: ''),
    );
    if (lastUser.content.isNotEmpty) {
      final prompt = lastUser.content;
      turns.removeLast();
      await send(
        modelId: modelId,
        systemPrompt: systemPrompt,
        userText: prompt,
      );
    }
  }

  Future<void> _stream(
    String modelId,
    List<Map<String, String>> messages,
  ) async {
    final completer = Completer<void>();
    _subscription = client
        .chatStream(modelId, messages)
        .listen(
          (token) {
            if (turns.isEmpty || turns.last.role != 'assistant') {
              return;
            }
            final current = turns.last.content;
            turns[turns.length - 1] = ChatTurn.assistant('$current$token');
            notifyListeners();
          },
          onError: (Object error, StackTrace stackTrace) {
            if (!completer.isCompleted) {
              completer.completeError(error, stackTrace);
            }
          },
          onDone: () {
            if (!completer.isCompleted) {
              completer.complete();
            }
          },
          cancelOnError: true,
        );
    await completer.future;
  }

  void stop() {
    _subscription?.cancel();
    _subscription = null;
    isGenerating = false;
    notifyListeners();
  }

  void clear() {
    turns.clear();
    lastError = null;
    notifyListeners();
  }

  List<Map<String, String>> _buildMessages(
    String systemPrompt,
    List<ChatTurn> sourceTurns,
  ) {
    final messages = <Map<String, String>>[];
    final system = systemPrompt.trim();
    if (system.isNotEmpty) {
      messages.add({'role': 'system', 'content': system});
    }
    for (final turn in sourceTurns) {
      messages.add({'role': turn.role, 'content': turn.content});
    }
    return messages;
  }
}
