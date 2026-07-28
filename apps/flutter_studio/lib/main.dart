import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

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
  final _setupPasswordController = TextEditingController();
  final _setupConfirmController = TextEditingController();
  final _systemController = TextEditingController(
    text: 'You are a concise and reliable local assistant.',
  );
  final _client = LlmStudioClient(defaultApiBase);
  final BackendService _backend = createBackendService();

  int _pageIndex = 0;
  bool _loading = false;
  bool _requiresSetup = false;
  String? _error;
  String _backendStatus = 'Backend has not started yet.';
  Map<String, dynamic>? _runtime;
  Map<String, dynamic>? _currentModel;
  Map<String, dynamic>? _gpuScheduler;
  List<dynamic> _models = const [];
  String? _selectedModelId;
  final List<ChatTurn> _turns = [];

  @override
  void initState() {
    super.initState();
    if (widget.autoRefresh) {
      unawaited(_bootstrap());
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
    _setupPasswordController.dispose();
    _setupConfirmController.dispose();
    super.dispose();
  }

  Future<void> _bootstrap() async {
    await _loadPreferences();
    await _refreshAll();
  }

  Future<void> _loadPreferences() async {
    final prefs = await SharedPreferences.getInstance();
    _apiBaseController.text =
        prefs.getString('llm_studio.api_base_url') ?? defaultApiBase;
    _userIdController.text = prefs.getString('llm_studio.user_id') ?? 'admin';
    _apiKeyController.text = prefs.getString('llm_studio.api_key') ?? '';
    _selectedModelId = prefs.getString('llm_studio.selected_model_id');
    _syncClientAuth();
  }

  Future<void> _savePreferences() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(
      'llm_studio.api_base_url',
      _apiBaseController.text.trim(),
    );
    await prefs.setString('llm_studio.user_id', _userIdController.text.trim());
    await prefs.setString('llm_studio.api_key', _apiKeyController.text.trim());
    final selected = _selectedModelId;
    if (selected == null || selected.isEmpty) {
      await prefs.remove('llm_studio.selected_model_id');
    } else {
      await prefs.setString('llm_studio.selected_model_id', selected);
    }
  }

  void _syncClientAuth() {
    _client.baseUrl = _apiBaseController.text.trim();
    _client.userId = _userIdController.text.trim();
    _client.apiKey = _apiKeyController.text.trim();
  }

  Future<void> _refreshAll() async {
    _syncClientAuth();
    await _guarded(() async {
      setState(() => _backendStatus = 'Starting backend...');
      final backend = await _backend.ensureStarted(apiBase: _client.baseUrl);
      setState(() => _backendStatus = backend.message);
      final setup = await _client.setupStatus();
      if (setup['requires_setup'] == true) {
        setState(() {
          _requiresSetup = true;
          _runtime = null;
          _models = const [];
          _currentModel = null;
          _gpuScheduler = null;
        });
        return;
      }
      setState(() => _requiresSetup = false);
      final runtime = await _client.runtime();
      final models = await _client.models();
      final current = await _client.currentModel();
      final gpuScheduler = await _client.gpuScheduler();
      setState(() {
        _runtime = runtime;
        _models = models;
        _currentModel = current;
        _gpuScheduler = gpuScheduler;
        if (_selectedModelId != null &&
            !models.any(
              (model) => model is Map && model['id'] == _selectedModelId,
            )) {
          _selectedModelId = null;
        }
      });
      await _savePreferences();
    });
  }

  Future<void> _initializeSetup() async {
    final password = _setupPasswordController.text;
    final confirm = _setupConfirmController.text;
    if (password.isEmpty || password != confirm) {
      setState(() => _error = 'Passwords do not match.');
      return;
    }
    await _guarded(() async {
      _syncClientAuth();
      final result = await _client.initialize(adminPassword: password);
      _userIdController.text = '${result['user_id'] ?? 'admin'}';
      _apiKeyController.text = '${result['api_key'] ?? ''}';
      _setupPasswordController.clear();
      _setupConfirmController.clear();
      _requiresSetup = false;
      _syncClientAuth();
      await _savePreferences();
      await _refreshAll();
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
        final modelId =
            _selectedModelId ??
            (_currentModel?['loaded'] == true
                ? '${_currentModel?['model_id']}'
                : '');
        if (modelId.isEmpty) {
          throw StudioApiException(
            'Please load a model on the Models page first.',
          );
        }
        final text = await _client.chat(modelId, messages);
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

  Future<void> _scanModels() async {
    await _guarded(() async {
      await _client.scanModels();
      await _refreshAll();
    });
  }

  Future<void> _loadModel(String modelId) async {
    await _guarded(() async {
      final current = await _client.loadModel(modelId);
      _selectedModelId = '${current['model_id'] ?? modelId}';
      await _savePreferences();
      await _refreshAll();
    });
  }

  Future<void> _unloadModel() async {
    final modelId =
        _selectedModelId ??
        (_currentModel?['loaded'] == true
            ? '${_currentModel?['model_id']}'
            : '');
    if (modelId.isEmpty) {
      return;
    }
    await _guarded(() async {
      await _client.unloadModel(modelId);
      _selectedModelId = null;
      await _savePreferences();
      await _refreshAll();
    });
  }

  Future<void> _selectModel(String modelId) async {
    setState(() => _selectedModelId = modelId);
    await _savePreferences();
  }

  Future<void> _clearAuth() async {
    _apiKeyController.clear();
    _selectedModelId = null;
    await _savePreferences();
    _syncClientAuth();
    setState(() {
      _runtime = null;
      _currentModel = null;
      _gpuScheduler = null;
      _error = 'Authentication has been cleared.';
    });
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
    if (_requiresSetup) {
      return _SetupPage(
        passwordController: _setupPasswordController,
        confirmController: _setupConfirmController,
        loading: _loading,
        error: _error,
        onInitialize: _initializeSetup,
        backendStatus: _backendStatus,
      );
    }
    final pages = [
      _DashboardPage(
        runtime: _runtime,
        models: _models,
        gpuScheduler: _gpuScheduler,
      ),
      _ModelsPage(
        models: _models,
        currentModel: _currentModel,
        selectedModelId: _selectedModelId,
        onRefresh: _refreshAll,
        onScan: _scanModels,
        onLoad: _loadModel,
        onUnload: _unloadModel,
        onSelect: _selectModel,
      ),
      _ChatPage(
        turns: _turns,
        chatController: _chatController,
        systemController: _systemController,
        selectedModelId: _selectedModelId,
        currentModel: _currentModel,
        onSend: _sendChat,
        onClear: () => setState(_turns.clear),
      ),
      _SettingsPage(
        apiBaseController: _apiBaseController,
        userIdController: _userIdController,
        apiKeyController: _apiKeyController,
        backendLogs: _backend.recentLogs(),
        onApply: _refreshAll,
        onClearAuth: _clearAuth,
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

  Future<Map<String, dynamic>> setupStatus() async {
    final response = await http
        .get(Uri.parse('$baseUrl/v1/setup/status'))
        .timeout(const Duration(seconds: 8));
    return _decodeMap(response);
  }

  Future<Map<String, dynamic>> initialize({
    required String adminPassword,
  }) async {
    final response = await http
        .post(
          Uri.parse('$baseUrl/v1/setup/initialize'),
          headers: {'content-type': 'application/json'},
          body: jsonEncode({
            'admin_password': adminPassword,
            'display_name': 'Admin',
          }),
        )
        .timeout(const Duration(seconds: 15));
    return _decodeMap(response);
  }

  Future<void> scanModels() async {
    final response = await http
        .post(Uri.parse('$baseUrl/v1/models/scan'), headers: _authHeaders())
        .timeout(const Duration(seconds: 15));
    _decodeMap(response);
  }

  Future<Map<String, dynamic>> loadModel(String modelId) async {
    final response = await http
        .post(
          Uri.parse('$baseUrl/v1/models/${Uri.encodeComponent(modelId)}/load'),
          headers: {..._authHeaders(), 'content-type': 'application/json'},
          body: jsonEncode({'strategy': 'auto'}),
        )
        .timeout(const Duration(minutes: 10));
    return _decodeMap(response);
  }

  Future<void> unloadModel(String modelId) async {
    final response = await http
        .post(
          Uri.parse('$baseUrl/v1/models/unload'),
          headers: {..._authHeaders(), 'content-type': 'application/json'},
          body: jsonEncode({'model': modelId}),
        )
        .timeout(const Duration(seconds: 30));
    _decodeMap(response);
  }

  Future<Map<String, dynamic>> currentModel() async {
    final response = await http
        .get(Uri.parse('$baseUrl/v1/models/current'), headers: _authHeaders())
        .timeout(const Duration(seconds: 8));
    return _decodeMap(response);
  }

  Future<Map<String, dynamic>> gpuScheduler() async {
    final response = await http
        .get(Uri.parse('$baseUrl/v1/gpu/scheduler'), headers: _authHeaders())
        .timeout(const Duration(seconds: 8));
    return _decodeMap(response);
  }

  Future<String> chat(
    String modelId,
    List<Map<String, String>> messages,
  ) async {
    final response = await http
        .post(
          Uri.parse('$baseUrl/v1/chat/completions'),
          headers: {..._authHeaders(), 'content-type': 'application/json'},
          body: jsonEncode({
            'model': modelId,
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
        final code = '${error['code']}';
        final message = switch (code) {
          'PERMISSION_DENIED' => '当前 API Key 权限不足。',
          'UPLOAD_FILE_TOO_LARGE' => '上传文件过大。',
          'GPU_BUSY' => 'GPU 正在执行其他任务，请稍后重试。',
          _ => '${error['message']}',
        };
        throw StudioApiException('$code: $message');
      }
      throw StudioApiException('HTTP ${response.statusCode}: ${response.body}');
    }
    if (body is Map<String, dynamic>) {
      return body;
    }
    throw StudioApiException('API response is not a JSON object.');
  }

  Map<String, String> authHeadersForTesting() => _authHeaders();

  Map<String, String> _authHeaders() {
    if (apiKey.isEmpty) {
      return const {};
    }
    return {
      'X-User-ID': userId,
      'X-API-Key': apiKey,
      'Authorization': 'Bearer $apiKey',
    };
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

class _SetupPage extends StatelessWidget {
  const _SetupPage({
    required this.passwordController,
    required this.confirmController,
    required this.loading,
    required this.error,
    required this.onInitialize,
    required this.backendStatus,
  });

  final TextEditingController passwordController;
  final TextEditingController confirmController;
  final bool loading;
  final String? error;
  final VoidCallback onInitialize;
  final String backendStatus;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 460),
          child: Card(
            elevation: 0,
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Text(
                    'Initialize LLM Studio',
                    style: TextStyle(fontSize: 24, fontWeight: FontWeight.w700),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    backendStatus,
                    style: const TextStyle(color: Colors.black54),
                  ),
                  const SizedBox(height: 16),
                  const Text(
                    'First use requires a local admin account and API key.',
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: passwordController,
                    obscureText: true,
                    decoration: const InputDecoration(
                      labelText: 'Admin password',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: confirmController,
                    obscureText: true,
                    decoration: const InputDecoration(
                      labelText: 'Confirm password',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  if (error != null) ...[
                    const SizedBox(height: 12),
                    Text(error!, style: const TextStyle(color: Colors.red)),
                  ],
                  const SizedBox(height: 16),
                  FilledButton.icon(
                    onPressed: loading ? null : onInitialize,
                    icon: loading
                        ? const SizedBox(
                            width: 16,
                            height: 16,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.check),
                    label: const Text('Initialize'),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
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
  const _ModelsPage({
    required this.models,
    required this.currentModel,
    required this.selectedModelId,
    required this.onRefresh,
    required this.onScan,
    required this.onLoad,
    required this.onUnload,
    required this.onSelect,
  });

  final List<dynamic> models;
  final Map<String, dynamic>? currentModel;
  final String? selectedModelId;
  final VoidCallback onRefresh;
  final VoidCallback onScan;
  final Future<void> Function(String modelId) onLoad;
  final VoidCallback onUnload;
  final Future<void> Function(String modelId) onSelect;

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
              OutlinedButton.icon(
                onPressed: onScan,
                icon: const Icon(Icons.manage_search),
                label: const Text('Scan'),
              ),
              const SizedBox(width: 8),
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
                      final id = '${map['id'] ?? ''}';
                      final status = '${map['status'] ?? 'unknown'}';
                      final isReady = status == 'ready';
                      final isLoaded =
                          currentModel?['loaded'] == true &&
                          currentModel?['model_id'] == id;
                      final isSelected = selectedModelId == id;
                      return Card(
                        elevation: 0,
                        child: ListTile(
                          leading: Icon(
                            isLoaded ? Icons.check_circle : Icons.view_in_ar,
                          ),
                          title: Text(
                            '${map['display_name'] ?? map['id'] ?? map['path'] ?? 'unknown'}',
                          ),
                          subtitle: Text(
                            '${map['format'] ?? 'unknown'} - ${map['status'] ?? 'unknown'}\n${map['path'] ?? ''}',
                          ),
                          isThreeLine: true,
                          trailing: Wrap(
                            spacing: 8,
                            children: [
                              if (isSelected) const Chip(label: Text('Chat')),
                              TextButton(
                                onPressed: id.isEmpty
                                    ? null
                                    : () => onSelect(id),
                                child: const Text('Use'),
                              ),
                              FilledButton.tonal(
                                onPressed: isReady && !isLoaded
                                    ? () => onLoad(id)
                                    : null,
                                child: Text(isLoaded ? 'Loaded' : 'Load'),
                              ),
                              if (isLoaded)
                                IconButton(
                                  onPressed: onUnload,
                                  icon: const Icon(Icons.eject),
                                  tooltip: 'Unload',
                                ),
                            ],
                          ),
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
    required this.selectedModelId,
    required this.currentModel,
    required this.onSend,
    required this.onClear,
  });

  final List<ChatTurn> turns;
  final TextEditingController chatController;
  final TextEditingController systemController;
  final String? selectedModelId;
  final Map<String, dynamic>? currentModel;
  final VoidCallback onSend;
  final VoidCallback onClear;

  @override
  Widget build(BuildContext context) {
    final loaded = currentModel?['loaded'] == true;
    final modelId =
        selectedModelId ?? (loaded ? '${currentModel?['model_id'] ?? ''}' : '');
    final canChat = modelId.isNotEmpty && loaded;
    return _PagePadding(
      child: Column(
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  canChat
                      ? 'Current model: $modelId'
                      : 'Please load a model on the Models page.',
                  style: const TextStyle(fontWeight: FontWeight.w700),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          TextField(
            controller: systemController,
            enabled: canChat,
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
                  enabled: canChat,
                  minLines: 1,
                  maxLines: 4,
                  decoration: const InputDecoration(
                    hintText: 'Message',
                    border: OutlineInputBorder(),
                  ),
                  onSubmitted: (_) {
                    if (canChat) {
                      onSend();
                    }
                  },
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
                onPressed: canChat ? onSend : null,
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
    required this.backendLogs,
    required this.onApply,
    required this.onClearAuth,
  });

  final TextEditingController apiBaseController;
  final TextEditingController userIdController;
  final TextEditingController apiKeyController;
  final List<String> backendLogs;
  final VoidCallback onApply;
  final VoidCallback onClearAuth;

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
          const SizedBox(height: 8),
          OutlinedButton.icon(
            onPressed: onClearAuth,
            icon: const Icon(Icons.key_off),
            label: const Text('Clear auth'),
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
          const SizedBox(height: 24),
          const Text(
            'Backend logs',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700),
          ),
          const SizedBox(height: 8),
          Expanded(
            child: DecoratedBox(
              decoration: BoxDecoration(
                color: const Color(0xff111827),
                borderRadius: BorderRadius.circular(8),
              ),
              child: ListView(
                padding: const EdgeInsets.all(12),
                children: backendLogs.isEmpty
                    ? const [
                        Text(
                          'No backend logs captured yet.',
                          style: TextStyle(color: Colors.white70),
                        ),
                      ]
                    : backendLogs
                          .map(
                            (line) => Text(
                              line,
                              style: const TextStyle(
                                color: Colors.white70,
                                fontFamily: 'monospace',
                              ),
                            ),
                          )
                          .toList(),
              ),
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
