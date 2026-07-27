import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

import 'backend/backend_service.dart';

const defaultApiBase = String.fromEnvironment(
  'LLM_STUDIO_API_BASE',
  defaultValue: 'http://127.0.0.1:8000',
);

void main() {
  runApp(const LlmStudioApp());
}

class LlmStudioApp extends StatelessWidget {
  const LlmStudioApp({super.key, this.autoRefresh = true});

  final bool autoRefresh;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'LLM Studio',
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xff2563eb)),
        scaffoldBackgroundColor: const Color(0xfff7f8fb),
      ),
      home: StudioShell(autoRefresh: autoRefresh),
    );
  }
}

class StudioShell extends StatefulWidget {
  const StudioShell({super.key, this.autoRefresh = true});

  final bool autoRefresh;

  @override
  State<StudioShell> createState() => _StudioShellState();
}

class _StudioShellState extends State<StudioShell> {
  final _apiBaseController = TextEditingController(text: defaultApiBase);
  final _userIdController = TextEditingController(text: 'admin');
  final _apiKeyController = TextEditingController();
  final _chatController = TextEditingController();
  final _systemController = TextEditingController(
    text: 'You are a concise and reliable local assistant.',
  );
  final _client = LlmStudioClient(defaultApiBase);
  final BackendService _backend = createBackendService();

  int _pageIndex = 0;
  bool _loading = false;
  String? _error;
  String _backendStatus = 'Backend has not started yet.';
  Map<String, dynamic>? _runtime;
  List<dynamic> _models = const [];
  final List<ChatTurn> _turns = [];

  @override
  void initState() {
    super.initState();
    if (widget.autoRefresh) {
      unawaited(_refreshAll());
    }
  }

  @override
  void dispose() {
    unawaited(_backend.stop());
    _apiBaseController.dispose();
    _userIdController.dispose();
    _apiKeyController.dispose();
    _chatController.dispose();
    _systemController.dispose();
    super.dispose();
  }

  Future<void> _refreshAll() async {
    _client.baseUrl = _apiBaseController.text.trim();
    _client.userId = _userIdController.text.trim();
    _client.apiKey = _apiKeyController.text.trim();
    await _guarded(() async {
      setState(() => _backendStatus = 'Starting backend...');
      final backend = await _backend.ensureStarted(apiBase: _client.baseUrl);
      setState(() => _backendStatus = backend.message);
      final runtime = await _client.runtime();
      final models = await _client.models();
      setState(() {
        _runtime = runtime;
        _models = models;
      });
    });
  }

  Future<void> _sendChat() async {
    final prompt = _chatController.text.trim();
    if (prompt.isEmpty) {
      return;
    }
    _chatController.clear();
    final nextTurns = [..._turns, ChatTurn.user(prompt)];
    setState(() {
      _turns
        ..clear()
        ..addAll(nextTurns)
        ..add(ChatTurn.assistant('Generating...'));
    });

    await _guarded(
      () async {
        final messages = <Map<String, String>>[];
        final system = _systemController.text.trim();
        if (system.isNotEmpty) {
          messages.add({'role': 'system', 'content': system});
        }
        for (final turn in nextTurns) {
          messages.add({'role': turn.role, 'content': turn.content});
        }
        final text = await _client.chat(messages);
        setState(() {
          _turns[_turns.length - 1] = ChatTurn.assistant(text);
        });
      },
      onError: () {
        setState(() {
          if (_turns.isNotEmpty && _turns.last.role == 'assistant') {
            _turns.removeLast();
          }
        });
      },
    );
  }

  Future<void> _guarded(
    Future<void> Function() action, {
    VoidCallback? onError,
  }) async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      await action();
    } catch (error) {
      onError?.call();
      setState(() => _error = error.toString());
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final pages = [
      _DashboardPage(runtime: _runtime, models: _models),
      _ModelsPage(models: _models, onRefresh: _refreshAll),
      _ChatPage(
        turns: _turns,
        chatController: _chatController,
        systemController: _systemController,
        onSend: _sendChat,
        onClear: () => setState(_turns.clear),
      ),
      _SettingsPage(
        apiBaseController: _apiBaseController,
        userIdController: _userIdController,
        apiKeyController: _apiKeyController,
        onApply: _refreshAll,
      ),
    ];

    return Scaffold(
      body: Row(
        children: [
          NavigationRail(
            selectedIndex: _pageIndex,
            onDestinationSelected: (index) =>
                setState(() => _pageIndex = index),
            labelType: NavigationRailLabelType.all,
            destinations: const [
              NavigationRailDestination(
                icon: Icon(Icons.monitor_heart_outlined),
                selectedIcon: Icon(Icons.monitor_heart),
                label: Text('Status'),
              ),
              NavigationRailDestination(
                icon: Icon(Icons.storage_outlined),
                selectedIcon: Icon(Icons.storage),
                label: Text('Models'),
              ),
              NavigationRailDestination(
                icon: Icon(Icons.chat_bubble_outline),
                selectedIcon: Icon(Icons.chat_bubble),
                label: Text('Chat'),
              ),
              NavigationRailDestination(
                icon: Icon(Icons.settings_outlined),
                selectedIcon: Icon(Icons.settings),
                label: Text('Settings'),
              ),
            ],
          ),
          const VerticalDivider(width: 1),
          Expanded(
            child: Column(
              children: [
                _TopBar(
                  loading: _loading,
                  backendStatus: _backendStatus,
                  onRefresh: _refreshAll,
                ),
                if (_error != null)
                  MaterialBanner(
                    content: Text(_error!),
                    leading: const Icon(Icons.error_outline),
                    actions: [
                      TextButton(
                        onPressed: () => setState(() => _error = null),
                        child: const Text('Dismiss'),
                      ),
                    ],
                  ),
                Expanded(child: pages[_pageIndex]),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class LlmStudioClient {
  LlmStudioClient(this.baseUrl);

  String baseUrl;
  String userId = 'admin';
  String apiKey = '';

  Future<Map<String, dynamic>> runtime() async {
    final response = await http
        .get(Uri.parse('$baseUrl/v1/runtime'), headers: _authHeaders())
        .timeout(const Duration(seconds: 8));
    return _decodeMap(response);
  }

  Future<List<dynamic>> models() async {
    final response = await http
        .get(Uri.parse('$baseUrl/v1/models'), headers: _authHeaders())
        .timeout(const Duration(seconds: 8));
    final body = _decodeMap(response);
    return (body['data'] as List?) ?? const [];
  }

  Future<String> chat(List<Map<String, String>> messages) async {
    final response = await http
        .post(
          Uri.parse('$baseUrl/v1/chat/completions'),
          headers: {..._authHeaders(), 'content-type': 'application/json'},
          body: jsonEncode({
            'model': 'auto',
            'messages': messages,
            'stream': false,
          }),
        )
        .timeout(const Duration(minutes: 5));
    final body = _decodeMap(response);
    final choices = body['choices'];
    if (choices is List && choices.isNotEmpty) {
      final message = choices.first['message'];
      if (message is Map && message['content'] is String) {
        return message['content'] as String;
      }
    }
    return jsonEncode(body);
  }

  Map<String, dynamic> _decodeMap(http.Response response) {
    final dynamic body = response.body.isEmpty
        ? <String, dynamic>{}
        : jsonDecode(response.body);
    if (response.statusCode >= 400) {
      if (body is Map && body['error'] is Map) {
        final error = body['error'] as Map;
        throw StudioApiException('${error['code']}: ${error['message']}');
      }
      throw StudioApiException('HTTP ${response.statusCode}: ${response.body}');
    }
    if (body is Map<String, dynamic>) {
      return body;
    }
    throw StudioApiException('API response is not a JSON object.');
  }

  Map<String, String> _authHeaders() {
    if (apiKey.isEmpty) {
      return const {};
    }
    return {'X-User-ID': userId, 'X-API-Key': apiKey};
  }
}

class StudioApiException implements Exception {
  StudioApiException(this.message);

  final String message;

  @override
  String toString() => message;
}

class ChatTurn {
  const ChatTurn({required this.role, required this.content});

  factory ChatTurn.user(String content) =>
      ChatTurn(role: 'user', content: content);

  factory ChatTurn.assistant(String content) =>
      ChatTurn(role: 'assistant', content: content);

  final String role;
  final String content;
}

class _TopBar extends StatelessWidget {
  const _TopBar({
    required this.loading,
    required this.backendStatus,
    required this.onRefresh,
  });

  final bool loading;
  final String backendStatus;
  final VoidCallback onRefresh;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 64,
      padding: const EdgeInsets.symmetric(horizontal: 20),
      alignment: Alignment.centerLeft,
      color: Colors.white,
      child: Row(
        children: [
          const Text(
            'LLM Studio',
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.w700),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              backendStatus,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(color: Colors.black54),
            ),
          ),
          if (loading)
            const SizedBox(
              width: 20,
              height: 20,
              child: CircularProgressIndicator(strokeWidth: 2),
            ),
          const SizedBox(width: 12),
          IconButton.filledTonal(
            onPressed: loading ? null : onRefresh,
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh',
          ),
        ],
      ),
    );
  }
}

class _DashboardPage extends StatelessWidget {
  const _DashboardPage({required this.runtime, required this.models});

  final Map<String, dynamic>? runtime;
  final List<dynamic> models;

  @override
  Widget build(BuildContext context) {
    final data = runtime ?? const <String, dynamic>{};
    return _PagePadding(
      child: GridView.count(
        crossAxisCount: MediaQuery.sizeOf(context).width > 1100 ? 4 : 2,
        crossAxisSpacing: 12,
        mainAxisSpacing: 12,
        childAspectRatio: 2.4,
        children: [
          _MetricTile(
            label: 'CUDA',
            value: '${data['cuda_available'] ?? 'unknown'}',
          ),
          _MetricTile(
            label: 'GPU',
            value: '${data['gpu_name'] ?? 'not detected'}',
          ),
          _MetricTile(
            label: 'BF16',
            value: '${data['bf16_supported'] ?? 'unknown'}',
          ),
          _MetricTile(label: 'Models', value: '${models.length}'),
          _MetricTile(
            label: 'Current model',
            value: '${data['current_model'] ?? 'none'}',
          ),
          _MetricTile(label: 'Backend', value: '${data['backend'] ?? 'none'}'),
          _MetricTile(label: 'Queue', value: '${data['queue_length'] ?? 0}'),
          _MetricTile(
            label: 'Concurrency',
            value: '${data['inference_concurrency'] ?? '-'}',
          ),
        ],
      ),
    );
  }
}

class _ModelsPage extends StatelessWidget {
  const _ModelsPage({required this.models, required this.onRefresh});

  final List<dynamic> models;
  final VoidCallback onRefresh;

  @override
  Widget build(BuildContext context) {
    return _PagePadding(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Text(
                'Local models',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700),
              ),
              const Spacer(),
              FilledButton.icon(
                onPressed: onRefresh,
                icon: const Icon(Icons.search),
                label: const Text('Refresh'),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Expanded(
            child: models.isEmpty
                ? const Center(
                    child: Text(
                      'No models found. Register or download a model first.',
                    ),
                  )
                : ListView.separated(
                    itemCount: models.length,
                    separatorBuilder: (_, _) => const SizedBox(height: 8),
                    itemBuilder: (context, index) {
                      final model = models[index];
                      final map = model is Map ? model : const {};
                      return Card(
                        elevation: 0,
                        child: ListTile(
                          leading: const Icon(Icons.view_in_ar),
                          title: Text(
                            '${map['display_name'] ?? map['id'] ?? map['path'] ?? 'unknown'}',
                          ),
                          subtitle: Text(
                            '${map['format'] ?? 'unknown'} - ${map['status'] ?? 'unknown'}\n${map['path'] ?? ''}',
                          ),
                          isThreeLine: true,
                          trailing: Text('${map['quantization'] ?? ''}'),
                        ),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }
}

class _ChatPage extends StatelessWidget {
  const _ChatPage({
    required this.turns,
    required this.chatController,
    required this.systemController,
    required this.onSend,
    required this.onClear,
  });

  final List<ChatTurn> turns;
  final TextEditingController chatController;
  final TextEditingController systemController;
  final VoidCallback onSend;
  final VoidCallback onClear;

  @override
  Widget build(BuildContext context) {
    return _PagePadding(
      child: Column(
        children: [
          TextField(
            controller: systemController,
            decoration: const InputDecoration(
              labelText: 'System Prompt',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 12),
          Expanded(
            child: DecoratedBox(
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(8),
              ),
              child: turns.isEmpty
                  ? const Center(child: Text('Start a multi-turn chat.'))
                  : ListView.builder(
                      padding: const EdgeInsets.all(12),
                      itemCount: turns.length,
                      itemBuilder: (context, index) {
                        final turn = turns[index];
                        final isUser = turn.role == 'user';
                        return Align(
                          alignment: isUser
                              ? Alignment.centerRight
                              : Alignment.centerLeft,
                          child: ConstrainedBox(
                            constraints: const BoxConstraints(maxWidth: 760),
                            child: Card(
                              elevation: 0,
                              color: isUser
                                  ? const Color(0xffdbeafe)
                                  : const Color(0xfff1f5f9),
                              child: Padding(
                                padding: const EdgeInsets.all(12),
                                child: Text(turn.content),
                              ),
                            ),
                          ),
                        );
                      },
                    ),
            ),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: chatController,
                  minLines: 1,
                  maxLines: 4,
                  decoration: const InputDecoration(
                    hintText: 'Message',
                    border: OutlineInputBorder(),
                  ),
                  onSubmitted: (_) => onSend(),
                ),
              ),
              const SizedBox(width: 8),
              IconButton.filledTonal(
                onPressed: onClear,
                icon: const Icon(Icons.delete_outline),
                tooltip: 'Clear',
              ),
              const SizedBox(width: 8),
              FilledButton.icon(
                onPressed: onSend,
                icon: const Icon(Icons.send),
                label: const Text('Send'),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _SettingsPage extends StatelessWidget {
  const _SettingsPage({
    required this.apiBaseController,
    required this.userIdController,
    required this.apiKeyController,
    required this.onApply,
  });

  final TextEditingController apiBaseController;
  final TextEditingController userIdController;
  final TextEditingController apiKeyController;
  final VoidCallback onApply;

  @override
  Widget build(BuildContext context) {
    return _PagePadding(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Connection settings',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: apiBaseController,
            decoration: const InputDecoration(
              labelText: 'FastAPI base URL',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 12),
          FilledButton.icon(
            onPressed: onApply,
            icon: const Icon(Icons.check),
            label: const Text('Apply'),
          ),
          const SizedBox(height: 24),
          const Text(
            'The Flutter desktop app starts and owns the local FastAPI service when it is not already running.',
          ),
          const SizedBox(height: 12),
          TextField(
            controller: userIdController,
            decoration: const InputDecoration(
              labelText: 'X-User-ID',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: apiKeyController,
            obscureText: true,
            decoration: const InputDecoration(
              labelText: 'X-API-Key',
              border: OutlineInputBorder(),
            ),
          ),
        ],
      ),
    );
  }
}

class _MetricTile extends StatelessWidget {
  const _MetricTile({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 0,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(label, style: const TextStyle(color: Colors.black54)),
            const SizedBox(height: 8),
            Text(
              value,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700),
            ),
          ],
        ),
      ),
    );
  }
}

class _PagePadding extends StatelessWidget {
  const _PagePadding({required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Padding(padding: const EdgeInsets.all(20), child: child);
  }
}
