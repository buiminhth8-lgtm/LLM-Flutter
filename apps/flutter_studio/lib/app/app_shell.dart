import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';

import '../core/api/api_client.dart';
import '../core/api/api_exception.dart';
import '../core/backend/backend_service.dart';
import '../core/config/app_settings_store.dart';
import '../features/adapters/adapters_page.dart';
import '../features/benchmarks/benchmarks_page.dart';
import '../features/chat/chat_controller.dart';
import '../features/chat/chat_page.dart';
import '../features/diagnostics/diagnostics_page.dart';
import '../features/downloads/downloads_page.dart';
import '../features/models/models_page.dart';
import '../features/rag/rag_page.dart';
import '../features/settings/settings_page.dart';
import '../features/setup/setup_page.dart';
import '../features/status/status_page.dart';
import '../features/storage/storage_page.dart';

class StudioShell extends StatefulWidget {
  const StudioShell({
    super.key,
    this.autoRefresh = true,
    this.initialRequiresSetup = false,
  });

  final bool autoRefresh;
  final bool initialRequiresSetup;

  @override
  State<StudioShell> createState() => _StudioShellState();
}

class _StudioShellState extends State<StudioShell> {
  final _settingsStore = AppSettingsStore();
  final _apiBaseController = TextEditingController(text: defaultApiBase);
  final _userIdController = TextEditingController(text: 'admin');
  final _apiKeyController = TextEditingController();
  final _chatInputController = TextEditingController();
  final _downloadRepoController = TextEditingController();
  final _downloadRevisionController = TextEditingController();
  final _localPythonController = TextEditingController();
  final _localBackendRootController = TextEditingController();
  final _ragQueryController = TextEditingController();
  final _setupPasswordController = TextEditingController();
  final _setupConfirmController = TextEditingController();
  final _systemController = TextEditingController(
    text: 'You are a concise and reliable local assistant.',
  );
  final _client = LlmStudioClient(defaultApiBase);
  final BackendService _backend = createBackendService();
  late final ChatController _chat = ChatController(_client);

  int _pageIndex = 0;
  bool _loading = false;
  bool _initialSetupCheckDone = false;
  bool _requiresSetup = false;
  bool _authRequired = false;
  bool _autoStartBackend = true;
  bool _closeBackendOnExit = true;
  String _backendMode = 'local';
  String? _error;
  String _backendStatus = 'Backend has not started yet.';
  String? _selectedModelId;
  String? _ragResult;
  String? _diagnosticsResult;
  Map<String, dynamic>? _runtime;
  Map<String, dynamic>? _currentModel;
  Map<String, dynamic>? _gpuScheduler;
  Map<String, dynamic>? _storage;
  Map<String, dynamic>? _cleanupPreview;
  List<dynamic> _models = const [];
  List<dynamic> _jobs = const [];
  List<dynamic> _downloads = const [];
  List<dynamic> _adapters = const [];
  List<dynamic> _benchmarks = const [];
  List<dynamic> _capabilities = const [];

  @override
  void initState() {
    super.initState();
    _initialSetupCheckDone = widget.initialRequiresSetup || !widget.autoRefresh;
    _requiresSetup = widget.initialRequiresSetup;
    _chat.addListener(_onChatChanged);
    if (widget.autoRefresh) {
      unawaited(_bootstrap());
    }
  }

  @override
  void dispose() {
    _chat.removeListener(_onChatChanged);
    _chat.dispose();
    if (_closeBackendOnExit) {
      unawaited(_backend.stop());
    }
    _apiBaseController.dispose();
    _userIdController.dispose();
    _apiKeyController.dispose();
    _chatInputController.dispose();
    _downloadRepoController.dispose();
    _downloadRevisionController.dispose();
    _localPythonController.dispose();
    _localBackendRootController.dispose();
    _ragQueryController.dispose();
    _systemController.dispose();
    _setupPasswordController.dispose();
    _setupConfirmController.dispose();
    super.dispose();
  }

  void _onChatChanged() {
    if (mounted) {
      setState(() {});
    }
  }

  Future<void> _bootstrap() async {
    await _loadPreferences();
    await _refreshAll();
  }

  Future<void> _loadPreferences() async {
    final settings = await _settingsStore.load();
    _apiBaseController.text = settings.apiBaseUrl;
    _userIdController.text = settings.userId;
    _apiKeyController.text = settings.apiKey;
    _selectedModelId = settings.selectedModelId;
    _autoStartBackend = settings.autoStartBackend;
    _closeBackendOnExit = settings.closeBackendOnExit;
    _backendMode = settings.backendMode;
    _localPythonController.text = settings.localPythonPath;
    _localBackendRootController.text = settings.localBackendRoot;
    _chat.streamingEnabled = settings.chatStreamingEnabled;
    _syncClientAuth();
  }

  Future<void> _savePreferences() async {
    await _settingsStore.save(
      AppSettings(
        apiBaseUrl: _apiBaseController.text.trim(),
        userId: _userIdController.text.trim(),
        apiKey: _apiKeyController.text.trim(),
        selectedModelId: _selectedModelId,
        chatStreamingEnabled: _chat.streamingEnabled,
        autoStartBackend: _autoStartBackend,
        closeBackendOnExit: _closeBackendOnExit,
        backendMode: _backendMode,
        localPythonPath: _localPythonController.text.trim(),
        localBackendRoot: _localBackendRootController.text.trim(),
      ),
    );
  }

  void _syncClientAuth() {
    _client.baseUrl = _apiBaseController.text.trim();
    _client.userId = _userIdController.text.trim();
    _client.apiKey = _apiKeyController.text.trim();
  }

  Future<void> _refreshAll() async {
    _syncClientAuth();
    await _guarded(() async {
      if (_backendMode == 'local' && _autoStartBackend) {
        setState(() => _backendStatus = 'Starting backend...');
        final backend = await _backend.ensureStarted(
          apiBase: _client.baseUrl,
          localPythonPath: _localPythonController.text.trim(),
          localBackendRoot: _localBackendRootController.text.trim(),
        );
        setState(() => _backendStatus = backend.message);
      } else {
        setState(() => _backendStatus = 'Using remote backend.');
      }
      final setup = await _client.setupStatus();
      if (setup['requires_setup'] == true) {
        setState(() {
          _initialSetupCheckDone = true;
          _requiresSetup = true;
          _authRequired = false;
          _runtime = null;
          _models = const [];
          _jobs = const [];
          _currentModel = null;
          _gpuScheduler = null;
        });
        return;
      }
      setState(() {
        _initialSetupCheckDone = true;
        _requiresSetup = false;
        _authRequired = _apiKeyController.text.trim().isEmpty;
      });
      if (_apiKeyController.text.trim().isEmpty) {
        return;
      }
      final results = await Future.wait<dynamic>([
        _client.runtime(),
        _client.models(),
        _client.currentModel(),
        _client.gpuScheduler(),
        _client.jobs(),
        _client.capabilities(),
        _client.downloads().catchError((_) => const []),
        _client.adapters().catchError((_) => const []),
        _client.benchmarks().catchError((_) => const []),
        _client.storage().catchError((_) => const <String, dynamic>{}),
      ]);
      setState(() {
        _runtime = results[0] as Map<String, dynamic>;
        _models = results[1] as List<dynamic>;
        _currentModel = results[2] as Map<String, dynamic>;
        _gpuScheduler = results[3] as Map<String, dynamic>;
        _jobs = results[4] as List<dynamic>;
        _capabilities = results[5] as List<dynamic>;
        _downloads = results[6] as List<dynamic>;
        _adapters = results[7] as List<dynamic>;
        _benchmarks = results[8] as List<dynamic>;
        _storage = results[9] as Map<String, dynamic>;
        if (_selectedModelId != null &&
            !_models.any(
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
      setState(() => _error = '两次输入的管理员密码不一致。');
      return;
    }
    await _guarded(() async {
      final result = await _client.initialize(adminPassword: password);
      _userIdController.text = '${result['user_id'] ?? 'admin'}';
      _apiKeyController.text = '${result['api_key'] ?? ''}';
      _setupPasswordController.clear();
      _setupConfirmController.clear();
      _requiresSetup = false;
      _authRequired = false;
      _initialSetupCheckDone = true;
      _syncClientAuth();
      await _savePreferences();
      await _refreshAll();
    });
  }

  Future<void> _sendChat() async {
    final prompt = _chatInputController.text.trim();
    if (prompt.isEmpty) {
      return;
    }
    final modelId =
        _selectedModelId ??
        (_currentModel?['loaded'] == true
            ? '${_currentModel?['model_id']}'
            : '');
    if (modelId.isEmpty) {
      setState(() => _error = 'Please load a model on the Models page first.');
      return;
    }
    _chatInputController.clear();
    await _guarded(() async {
      await _chat.send(
        modelId: modelId,
        systemPrompt: _systemController.text,
        userText: prompt,
      );
      await _savePreferences();
    });
  }

  Future<void> _regenerateChat() async {
    final modelId =
        _selectedModelId ??
        (_currentModel?['loaded'] == true
            ? '${_currentModel?['model_id']}'
            : '');
    if (modelId.isEmpty) {
      return;
    }
    await _guarded(() async {
      await _chat.regenerate(
        modelId: modelId,
        systemPrompt: _systemController.text,
      );
    });
  }

  Future<void> _scanModels() async => _guarded(() async {
    await _client.scanModels();
    await _refreshAll();
  });

  Future<void> _loadModel(String modelId) async => _guarded(() async {
    final current = await _client.loadModel(modelId);
    _selectedModelId = '${current['model_id'] ?? modelId}';
    await _savePreferences();
    await _refreshAll();
  });

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

  String _activeModelId() {
    return _selectedModelId ??
        (_currentModel?['loaded'] == true
            ? '${_currentModel?['model_id']}'
            : '');
  }

  Future<void> _deleteModel(String modelId) async => _guarded(() async {
    await _client.deleteModel(modelId, confirm: true);
    if (_selectedModelId == modelId) {
      _selectedModelId = null;
    }
    await _refreshAll();
  });

  Future<void> _startDownload() async => _guarded(() async {
    await _client.startDownload(
      repoId: _downloadRepoController.text.trim(),
      revision: _downloadRevisionController.text.trim(),
    );
    await _refreshAll();
  });

  Future<void> _cancelDownload(String id) async => _guarded(() async {
    await _client.cancelDownload(id);
    await _refreshAll();
  });

  Future<void> _retryDownload(String id) async => _guarded(() async {
    await _client.retryDownload(id);
    await _refreshAll();
  });

  Future<void> _cancelJob(String id) async => _guarded(() async {
    await _client.cancelJob(id);
    await _refreshAll();
  });

  Future<void> _scanAdapters() async => _guarded(() async {
    await _client.scanAdapters();
    await _refreshAll();
  });

  Future<void> _adapterAction(Future<void> Function(String modelId) action) async =>
      _guarded(() async {
        final modelId = _activeModelId();
        if (modelId.isEmpty) {
          throw StudioApiException(
            '请先加载或选择基础模型。',
            code: 'ADAPTER_MODEL_REQUIRED',
          );
        }
        await action(modelId);
        await _refreshAll();
      });

  Future<void> _startBenchmark() async => _guarded(() async {
    final modelId =
        _selectedModelId ??
        (_currentModel?['loaded'] == true
            ? '${_currentModel?['model_id']}'
            : '');
    if (modelId.isEmpty) {
      throw StudioApiException(
        'Please load a model before starting Benchmark.',
      );
    }
    await _client.startBenchmark(modelId: modelId);
    await _refreshAll();
  });

  Future<void> _queryRag() async => _guarded(() async {
    final result = await _client.ragQuery(_ragQueryController.text.trim());
    setState(() => _ragResult = result);
  });

  Future<void> _previewCleanup() async => _guarded(() async {
    final preview = await _client.cleanupPreview();
    setState(() => _cleanupPreview = preview);
  });

  Future<void> _cleanupStorage() async => _guarded(() async {
    await _client.cleanupStorage();
    _cleanupPreview = null;
    await _refreshAll();
  });

  Future<void> _exportDiagnostics() async => _guarded(() async {
    final result = await _client.exportDiagnostics();
    setState(
      () => _diagnosticsResult = const JsonEncoder.withIndent(
        '  ',
      ).convert(result),
    );
  });

  Future<void> _clearAuth() async {
    _apiKeyController.clear();
    _selectedModelId = null;
    await _savePreferences();
    _syncClientAuth();
    setState(() {
      _runtime = null;
      _currentModel = null;
      _gpuScheduler = null;
      _authRequired = true;
      _error = '认证信息已清除，请重新填写 API Key。';
    });
  }

  Future<void> _restartBackend() async => _guarded(() async {
    await _backend.stop();
    final result = await _backend.ensureStarted(
      apiBase: _client.baseUrl,
      localPythonPath: _localPythonController.text.trim(),
      localBackendRoot: _localBackendRootController.text.trim(),
    );
    setState(() => _backendStatus = result.message);
  });

  Future<void> _stopBackend() async => _guarded(() async {
    await _backend.stop();
    setState(() => _backendStatus = 'Backend stopped by Flutter.');
  });

  Future<void> _guarded(Future<void> Function() action) async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      await action();
    } catch (error) {
      if (error is AuthRequiredException) {
        await _handleAuthRequired(error);
      } else {
        setState(() {
          _initialSetupCheckDone = true;
          _error = error.toString();
        });
      }
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  Future<void> _handleAuthRequired(AuthRequiredException error) async {
    try {
      final setup = await _client.setupStatus();
      if (setup['requires_setup'] == true) {
        setState(() {
          _initialSetupCheckDone = true;
          _requiresSetup = true;
          _authRequired = false;
          _error = null;
        });
        return;
      }
    } catch (_) {
      // Preserve the original authentication error if setup status cannot be checked.
    }
    setState(() {
      _initialSetupCheckDone = true;
      _requiresSetup = false;
      _authRequired = true;
      _error = error.toString();
    });
  }

  @override
  Widget build(BuildContext context) {
    if (!_initialSetupCheckDone && widget.autoRefresh) {
      return Scaffold(
        body: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 460),
            child: Card(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    const Text(
                      '正在检查 LLM-Studio 初始化状态',
                      style: TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(height: 12),
                    Text(
                      _backendStatus,
                      style: const TextStyle(color: Colors.black54),
                    ),
                    const SizedBox(height: 18),
                    const LinearProgressIndicator(),
                  ],
                ),
              ),
            ),
          ),
        ),
      );
    }
    if (_requiresSetup) {
      return SetupPage(
        passwordController: _setupPasswordController,
        confirmController: _setupConfirmController,
        loading: _loading,
        error: _error,
        onInitialize: _initializeSetup,
        backendStatus: _backendStatus,
      );
    }

    final pages = [
      StatusPage(
        runtime: _runtime,
        models: _models,
        gpuScheduler: _gpuScheduler,
        jobs: _jobs,
        capabilities: _capabilities,
        onCancelJob: _cancelJob,
      ),
      ModelsPage(
        models: _models,
        currentModel: _currentModel,
        selectedModelId: _selectedModelId,
        onRefresh: _refreshAll,
        onScan: _scanModels,
        onLoad: _loadModel,
        onUnload: _unloadModel,
        onSelect: _selectModel,
        onRegisterExternal: () => setState(
          () => _error =
              'External model registration will use the backend register API in the next UI pass.',
        ),
        onMoveToTrash: _deleteModel,
      ),
      ChatPage(
        controller: _chat,
        inputController: _chatInputController,
        systemController: _systemController,
        selectedModelId: _selectedModelId,
        currentModel: _currentModel,
        onSend: _sendChat,
        onStop: _chat.stop,
        onClear: _chat.clear,
        onRegenerate: _regenerateChat,
        onStreamingChanged: (value) async {
          setState(() => _chat.streamingEnabled = value);
          await _savePreferences();
        },
      ),
      DownloadsPage(
        downloads: _downloads,
        repoController: _downloadRepoController,
        revisionController: _downloadRevisionController,
        onStart: _startDownload,
        onCancel: _cancelDownload,
        onRetry: _retryDownload,
        onRefresh: _refreshAll,
      ),
      RagPage(
        queryController: _ragQueryController,
        result: _ragResult,
        onQuery: _queryRag,
      ),
      AdaptersPage(
        adapters: _adapters,
        currentModel: _currentModel,
        hasModelContext: _activeModelId().isNotEmpty,
        onRefresh: _refreshAll,
        onScan: _scanAdapters,
        onLoad: (id) => _adapterAction((modelId) => _client.loadAdapter(id, modelId)),
        onActivate: (id) => _adapterAction((modelId) => _client.activateAdapter(id, modelId)),
        onDeactivate: (id) =>
            _adapterAction((modelId) => _client.deactivateAdapter(id, modelId: modelId)),
      ),
      BenchmarksPage(
        benchmarks: _benchmarks,
        currentModel: _currentModel,
        onStart: _startBenchmark,
        onRefresh: _refreshAll,
      ),
      StoragePage(
        storage: _storage,
        cleanupPreview: _cleanupPreview,
        onRefresh: _refreshAll,
        onPreview: _previewCleanup,
        onCleanup: _cleanupStorage,
      ),
      DiagnosticsPage(
        runtime: _runtime,
        capabilities: _capabilities,
        exportResult: _diagnosticsResult,
        onExport: _exportDiagnostics,
      ),
      SettingsPage(
        apiBaseController: _apiBaseController,
        userIdController: _userIdController,
        apiKeyController: _apiKeyController,
        localPythonController: _localPythonController,
        localBackendRootController: _localBackendRootController,
        backendMode: _backendMode,
        autoStartBackend: _autoStartBackend,
        closeBackendOnExit: _closeBackendOnExit,
        backendLogs: _backend.recentLogs(),
        onApply: () async {
          _syncClientAuth();
          await _savePreferences();
          await _refreshAll();
        },
        onClearAuth: _clearAuth,
        onRestartBackend: _restartBackend,
        onStopBackend: _stopBackend,
        onBackendModeChanged: (value) async {
          setState(() => _backendMode = value);
          await _savePreferences();
        },
        onAutoStartChanged: (value) async {
          setState(() => _autoStartBackend = value);
          await _savePreferences();
        },
        onCloseOnExitChanged: (value) async {
          setState(() => _closeBackendOnExit = value);
          await _savePreferences();
        },
      ),
    ];

    return Scaffold(
      body: Row(
        children: [
          SizedBox(
            width: 176,
            child: ListView(
              padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
              children: [
                _SideNavItem(
                  index: 0,
                  selectedIndex: _pageIndex,
                  icon: Icons.monitor_heart_outlined,
                  label: 'Status',
                  onSelected: (index) => setState(() => _pageIndex = index),
                ),
                _SideNavItem(
                  index: 1,
                  selectedIndex: _pageIndex,
                  icon: Icons.storage_outlined,
                  label: 'Models',
                  onSelected: (index) => setState(() => _pageIndex = index),
                ),
                _SideNavItem(
                  index: 2,
                  selectedIndex: _pageIndex,
                  icon: Icons.chat_bubble_outline,
                  label: 'Chat',
                  onSelected: (index) => setState(() => _pageIndex = index),
                ),
                _SideNavItem(
                  index: 3,
                  selectedIndex: _pageIndex,
                  icon: Icons.cloud_download_outlined,
                  label: 'Downloads',
                  onSelected: (index) => setState(() => _pageIndex = index),
                ),
                _SideNavItem(
                  index: 4,
                  selectedIndex: _pageIndex,
                  icon: Icons.article_outlined,
                  label: 'RAG',
                  onSelected: (index) => setState(() => _pageIndex = index),
                ),
                _SideNavItem(
                  index: 5,
                  selectedIndex: _pageIndex,
                  icon: Icons.extension_outlined,
                  label: 'Adapters',
                  onSelected: (index) => setState(() => _pageIndex = index),
                ),
                _SideNavItem(
                  index: 6,
                  selectedIndex: _pageIndex,
                  icon: Icons.speed_outlined,
                  label: 'Benchmark',
                  onSelected: (index) => setState(() => _pageIndex = index),
                ),
                _SideNavItem(
                  index: 7,
                  selectedIndex: _pageIndex,
                  icon: Icons.cleaning_services_outlined,
                  label: 'Storage',
                  onSelected: (index) => setState(() => _pageIndex = index),
                ),
                _SideNavItem(
                  index: 8,
                  selectedIndex: _pageIndex,
                  icon: Icons.bug_report_outlined,
                  label: 'Diagnostics',
                  onSelected: (index) => setState(() => _pageIndex = index),
                ),
                _SideNavItem(
                  index: 9,
                  selectedIndex: _pageIndex,
                  icon: Icons.settings_outlined,
                  label: 'Settings',
                  onSelected: (index) => setState(() => _pageIndex = index),
                ),
              ],
            ),
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
                if (_authRequired)
                  MaterialBanner(
                    content: const Text(
                      '后端已经初始化，但当前客户端没有可用 API Key。请在 Settings 中填写 API Key，或使用管理员密码恢复/重新生成 API Key。',
                    ),
                    leading: const Icon(Icons.lock_outline),
                    actions: [
                      TextButton(
                        onPressed: () => setState(() => _pageIndex = 9),
                        child: const Text('打开 Settings'),
                      ),
                    ],
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

class _SideNavItem extends StatelessWidget {
  const _SideNavItem({
    required this.index,
    required this.selectedIndex,
    required this.icon,
    required this.label,
    required this.onSelected,
  });

  final int index;
  final int selectedIndex;
  final IconData icon;
  final String label;
  final ValueChanged<int> onSelected;

  @override
  Widget build(BuildContext context) {
    final selected = index == selectedIndex;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: ListTile(
        dense: true,
        selected: selected,
        selectedTileColor: const Color(0xffdbeafe),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        leading: Icon(icon),
        title: Text(label),
        onTap: () => onSelected(index),
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
