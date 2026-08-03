import 'dart:async';

import 'package:flutter/material.dart';

import '../core/api/api_client.dart';
import '../core/api/api_exception.dart';
import '../core/config/app_settings_store.dart';
import '../core/logging/client_logger.dart';
import '../core/models/dto.dart';
import '../features/adapters/adapter_controller.dart';
import '../features/adapters/adapters_page.dart';
import '../features/benchmarks/benchmark_controller.dart';
import '../features/benchmarks/benchmarks_page.dart';
import '../features/chat/chat_controller.dart';
import '../features/chat/chat_page.dart';
import '../features/context_assembler/context_api_client.dart';
import '../features/context_assembler/context_assembler_page.dart';
import '../features/context_assembler/context_controller.dart';
import '../features/datasets/dataset_api_client.dart';
import '../features/datasets/dataset_builder_page.dart';
import '../features/datasets/dataset_controller.dart';
import '../features/diagnostics/diagnostics_controller.dart';
import '../features/diagnostics/diagnostics_page.dart';
import '../features/downloads/download_controller.dart';
import '../features/downloads/downloads_page.dart';
import '../features/finetune/finetune_api_client.dart';
import '../features/finetune/finetune_center_page.dart';
import '../features/finetune/finetune_controller.dart';
import '../features/jobs/job_controller.dart';
import '../features/models/model_controller.dart';
import '../features/models/models_page.dart';
import '../features/novels/novel_api_client.dart';
import '../features/novels/novel_controller.dart';
import '../features/novels/novel_projects_page.dart';
import '../features/prompt_studio/prompt_api_client.dart';
import '../features/prompt_studio/prompt_controller.dart';
import '../features/prompt_studio/prompt_studio_page.dart';
import '../features/rag/rag_controller.dart';
import '../features/rag/rag_page.dart';
import '../features/revisions/revision_api_client.dart';
import '../features/revisions/revision_controller.dart';
import '../features/revisions/revision_review_page.dart';
import '../features/settings/settings_controller.dart';
import '../features/settings/settings_page.dart';
import '../features/setup/setup_page.dart';
import '../features/status/status_controller.dart';
import '../features/status/status_page.dart';
import '../features/storage/storage_controller.dart';
import '../features/storage/storage_page.dart';
import '../features/writing/writing_api_client.dart';
import '../features/writing/writing_controller.dart';
import '../features/writing/writing_workspace_page.dart';
import 'app_routes.dart';
import 'app_shell_widgets.dart';
import 'backend_lifecycle_controller.dart';
import 'shell_controller.dart';
import 'shell_navigation_controller.dart';

class StudioShell extends StatefulWidget {
  const StudioShell({
    super.key,
    this.autoRefresh = true,
    this.initialRequiresSetup = false,
    this.client,
  });

  final bool autoRefresh;
  final bool initialRequiresSetup;
  final LlmStudioClient? client;

  @override
  State<StudioShell> createState() => _StudioShellState();
}

class _StudioShellState extends State<StudioShell> {
  late final ShellController _shell = ShellController(
    autoRefresh: widget.autoRefresh,
    initialRequiresSetup: widget.initialRequiresSetup,
  );
  final _navigation = ShellNavigationController();
  final _settings = SettingsController();
  final _backend = BackendLifecycleController();
  late final LlmStudioClient _client =
      widget.client ?? LlmStudioClient(defaultApiBase);

  final _chatInputController = TextEditingController();
  final _downloadRepoController = TextEditingController();
  final _downloadRevisionController = TextEditingController();
  final _downloadAllowController = TextEditingController();
  final _downloadIgnoreController = TextEditingController();
  String _downloadProvider = 'modelscope';
  final _systemController = TextEditingController(
    text: 'You are a concise and reliable local assistant.',
  );

  late final ChatController _chat = ChatController(_client);
  late final ModelController _models = ModelController(_client);
  late final StatusController _status = StatusController(_client);
  late final JobController _jobs = JobController(_client);
  late final DownloadController _downloads = DownloadController(_client);
  late final RagController _rag = RagController(_client);
  late final AdapterController _adapters = AdapterController(_client);
  late final BenchmarkController _benchmarks = BenchmarkController(_client);
  late final StorageController _storage = StorageController(_client);
  late final DiagnosticsController _diagnostics = DiagnosticsController(
    _client,
  );
  late final NovelController _novels = NovelController(NovelApiClient(_client));
  late final PromptController _prompts = PromptController(
    PromptApiClient(_client),
  );
  late final ContextController _contextAssembler = ContextController(
    ContextApiClient(_client),
  );
  late final RevisionApiClient _revisionApi = RevisionApiClient(_client);
  late final RevisionController _revisions = RevisionController(_revisionApi);
  late final DatasetController _datasets = DatasetController(
    DatasetApiClient(_client),
  );
  late final FinetuneController _finetune = FinetuneController(
    FinetuneApiClient(_client),
  );
  late final WritingController _writing = WritingController(
    WritingApiClient(_client),
    revisionApi: _revisionApi,
  );

  @override
  void initState() {
    super.initState();
    for (final controller in _notifiers) {
      controller.addListener(_onNotifierChanged);
    }
    if (widget.autoRefresh) {
      unawaited(_bootstrap());
    }
  }

  @override
  void dispose() {
    for (final controller in _notifiers) {
      controller.removeListener(_onNotifierChanged);
    }
    for (final controller in _featureControllers) {
      controller.dispose();
    }
    unawaited(_backend.stopIfConfigured(_settings.closeBackendOnExit));
    _shell.dispose();
    _navigation.dispose();
    _settings.dispose();
    _backend.dispose();
    _chatInputController.dispose();
    _downloadRepoController.dispose();
    _downloadRevisionController.dispose();
    _downloadAllowController.dispose();
    _downloadIgnoreController.dispose();
    _systemController.dispose();
    super.dispose();
  }

  List<ChangeNotifier> get _notifiers => [
    _shell,
    _navigation,
    _settings,
    _backend,
    ..._featureControllers,
  ];

  List<ChangeNotifier> get _featureControllers => [
    _chat,
    _models,
    _status,
    _jobs,
    _downloads,
    _rag,
    _adapters,
    _benchmarks,
    _storage,
    _diagnostics,
    _novels,
    _prompts,
    _contextAssembler,
    _writing,
    _revisions,
    _datasets,
    _finetune,
  ];

  void _onNotifierChanged() {
    if (mounted) {
      setState(() {});
    }
  }

  Future<void> _bootstrap() async {
    await _loadPreferences();
    await _refreshAll();
  }

  Future<void> _loadPreferences() async {
    final settings = await _settings.load();
    _models.restoreSelectedModel(settings.selectedModelId);
    _chat.streamingEnabled = settings.chatStreamingEnabled;
    _syncClientAuth();
  }

  Future<void> _savePreferences() async {
    await _settings.save(
      selectedModelId: _models.selectedModelId,
      chatStreamingEnabled: _chat.streamingEnabled,
    );
  }

  Future<void> _loadAuthUsers() async {
    await _guarded(() async {
      _syncClientAuth();
      await _settings.loadAuthUsers(_client);
    });
  }

  Future<RegeneratedApiKeyDto> _regenerateApiKey(String userId) async {
    RegeneratedApiKeyDto? result;
    await _guarded(() async {
      _syncClientAuth();
      result = await _settings.regenerateApiKey(_client, userId);
    });
    if (result == null) {
      throw StateError('API Key regeneration failed.');
    }
    return result!;
  }

  void _syncClientAuth() {
    _client.baseUrl = _settings.apiBaseController.text.trim();
    _client.userId = _settings.userIdController.text.trim();
    _client.apiKey = _settings.apiKeyController.text.trim();
  }

  Future<void> _refreshAll() async {
    _syncClientAuth();
    await _guarded(() async {
      await _backend.ensureStarted(
        apiBase: _client.baseUrl,
        localMode: _settings.backendMode == 'local',
        autoStart: _settings.autoStartBackend,
        localPythonPath: _settings.localPythonController.text.trim(),
        localBackendRoot: _settings.localBackendRootController.text.trim(),
      );

      final setup = await _client.setupStatus();
      if (setup['requires_setup'] == true) {
        _shell.showSetupRequired();
        _status.clear();
        _models.clear();
        _jobs.clear();
        return;
      }

      final apiKeyMissing = _settings.apiKeyController.text.trim().isEmpty;
      _shell.showAuthenticated(apiKeyMissing: apiKeyMissing);
      if (apiKeyMissing) {
        return;
      }

      try {
        await _settings.refreshCurrentUser(_client);
      } on AuthRequiredException {
        rethrow;
      } catch (error) {
        logClientError('Unable to refresh current auth user: $error');
      }
      await Future.wait([
        _status.refresh(),
        _models.refresh(),
        _jobs.refresh(),
        _downloads.refresh().catchError((_) {}),
        _adapters.refresh().catchError((_) {}),
        _benchmarks.refresh().catchError((_) {}),
        _storage.refresh().catchError((_) {}),
        if (_novelStudioAvailable()) _novels.refresh().catchError((_) {}),
        if (_promptStudioAvailable()) _prompts.refresh().catchError((_) {}),
        if (_contextAssemblerAvailable())
          _contextAssembler.refresh().catchError((_) {}),
        if (_writingWorkspaceAvailable()) _writing.refresh().catchError((_) {}),
        if (_revisionSystemAvailable()) _revisions.refresh().catchError((_) {}),
        if (_datasetBuilderAvailable()) _datasets.refresh().catchError((_) {}),
        if (_finetuneCenterAvailable()) _finetune.refresh().catchError((_) {}),
      ]);
      await _savePreferences();
    });
  }

  Future<void> _initializeSetup() async {
    final password = _shell.setupPasswordController.text;
    final confirm = _shell.setupConfirmController.text;
    if (password.isEmpty || password != confirm) {
      _shell.setError('两次输入的管理员密码不一致。');
      return;
    }
    await _guarded(() async {
      final result = await _client.initialize(adminPassword: password);
      _settings.userIdController.text = '${result['user_id'] ?? 'admin'}';
      _settings.apiKeyController.text = '${result['api_key'] ?? ''}';
      _shell.setupPasswordController.clear();
      _shell.setupConfirmController.clear();
      _shell.completeSetup();
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
    final modelId = _models.activeModelId();
    if (modelId.isEmpty) {
      _shell.setError('请先在 Models 页面加载模型。');
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
    final modelId = _models.activeModelId();
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
    await _models.scan();
    await _refreshAll();
  });

  Future<void> _loadModel(String modelId) async => _guarded(() async {
    await _models.load(modelId);
    await _savePreferences();
    await _refreshAll();
  });

  Future<void> _unloadModel() async {
    if (_models.activeModelId().isEmpty) {
      return;
    }
    await _guarded(() async {
      await _models.unload();
      await _savePreferences();
      await _refreshAll();
    });
  }

  Future<void> _selectModel(String modelId) async {
    await _models.select(modelId);
    await _savePreferences();
  }

  String _activeModelId() => _models.activeModelId();

  Future<void> _deleteModel(String modelId) async => _guarded(() async {
    await _models.delete(modelId);
    await _refreshAll();
  });

  Future<void> _startDownload() async => _guarded(() async {
    await _downloads.start(
      repoId: _downloadRepoController.text.trim(),
      provider: _downloadProvider,
      revision: _downloadRevisionController.text.trim(),
      allowPatterns: _splitPatterns(_downloadAllowController.text),
      ignorePatterns: _splitPatterns(_downloadIgnoreController.text),
    );
    await _refreshAll();
  });

  List<String>? _splitPatterns(String text) {
    final patterns = text
        .split(',')
        .map((item) => item.trim())
        .where((item) => item.isNotEmpty)
        .toList();
    return patterns.isEmpty ? null : patterns;
  }

  Future<void> _cancelDownload(String id) async => _guarded(() async {
    await _downloads.cancel(id);
    await _refreshAll();
  });

  Future<void> _retryDownload(String id) async => _guarded(() async {
    await _downloads.retry(id);
    await _refreshAll();
  });

  Future<void> _deleteDownloadRecord(String id) async => _guarded(() async {
    await _downloads.deleteRecord(id);
    await _refreshAll();
  });

  Future<void> _viewDownloadedModel(String modelId) async => _guarded(() async {
    await _models.select(modelId);
    _navigation.select(1);
  });

  Future<void> _cancelJob(String id) async => _guarded(() async {
    await _jobs.cancel(id);
    await _refreshAll();
  });

  Future<void> _scanAdapters() async => _guarded(() async {
    await _adapters.scan();
    await _refreshAll();
  });

  Future<void> _adapterAction(
    Future<void> Function(String modelId) action,
  ) async => _guarded(() async {
    final modelId = _activeModelId();
    if (modelId.isEmpty) {
      throw StudioApiException('请先加载或选择基础模型。', code: 'ADAPTER_MODEL_REQUIRED');
    }
    await action(modelId);
    await _refreshAll();
  });

  Future<void> _startBenchmark() async => _guarded(() async {
    final modelId = _models.activeModelId();
    if (modelId.isEmpty) {
      throw StudioApiException('请先加载模型，再启动 Benchmark。');
    }
    await _benchmarks.start(modelId);
    await _refreshAll();
  });

  Future<void> _queryRag() async => _guarded(() async {
    await _rag.query();
  });

  Future<void> _previewCleanup() async => _guarded(() async {
    await _storage.previewCleanup();
  });

  Future<void> _cleanupStorage() async => _guarded(() async {
    await _storage.cleanup();
    await _refreshAll();
  });

  Future<void> _exportDiagnostics() async => _guarded(() async {
    await _diagnostics.export();
  });

  Future<void> _clearAuth() async {
    _settings.clearApiKey();
    _models.restoreSelectedModel(null);
    await _savePreferences();
    _syncClientAuth();
    _status.clear();
    _models.clear();
    _navigation.select(settingsPageIndex);
    _shell.setAuthRequired('认证信息已清除，请重新填写 API Key。');
  }

  Future<void> _restartBackend() async => _guarded(() async {
    await _backend.restart(
      apiBase: _client.baseUrl,
      localPythonPath: _settings.localPythonController.text.trim(),
      localBackendRoot: _settings.localBackendRootController.text.trim(),
    );
  });

  Future<void> _stopBackend() async => _guarded(() async {
    await _backend.stop();
  });

  Future<void> _guarded(Future<void> Function() action) async {
    _shell.setLoading(true);
    _shell.clearError();
    try {
      await action();
    } catch (error) {
      logClientError(error);
      if (error is AuthRequiredException) {
        await _handleAuthRequired(error);
      } else {
        _shell.setError(error.toString());
      }
    } finally {
      if (mounted) {
        _shell.setLoading(false);
      }
    }
  }

  Future<void> _handleAuthRequired(AuthRequiredException error) async {
    try {
      final setup = await _client.setupStatus();
      if (setup['requires_setup'] == true) {
        _shell.showSetupRequired();
        return;
      }
    } catch (_) {
      // Preserve the original authentication error if setup status cannot be checked.
    }
    _navigation.select(settingsPageIndex);
    _shell.setAuthRequired('认证已失效，请重新登录或填写有效 API Key。');
  }

  String _topModelLabel() {
    final loaded = _models.currentModel?['loaded'] == true;
    final modelId =
        _models.selectedModelId ??
        (loaded ? '${_models.currentModel?['model_id'] ?? ''}' : '');
    return modelId.isEmpty ? 'No model loaded' : modelId;
  }

  String _topAdapterLabel() {
    final adapter =
        _models.currentModel?['adapter_id'] ?? _models.currentModel?['adapter'];
    final label = '${adapter ?? ''}'.trim();
    return label.isEmpty ? 'None' : label;
  }

  String _topGpuLabel() {
    final running = _status.state.gpuScheduler?['running'];
    if (running is List && running.isNotEmpty) {
      return 'Busy';
    }
    return 'Idle';
  }

  int _runningJobCount() {
    return _jobs.state.jobs.where((job) {
      if (job is! Map) {
        return false;
      }
      final status = '${job['status'] ?? ''}';
      return status == 'pending' ||
          status == 'running' ||
          status == 'cancelling';
    }).length;
  }

  bool _novelStudioAvailable() {
    return _status.state.capabilities.any((item) {
      if (item is! Map) {
        return false;
      }
      return item['name'] == 'novel_studio' &&
          item['status'] == 'partial' &&
          item['frontend_exposed'] == true;
    });
  }

  bool _promptStudioAvailable() {
    return _status.state.capabilities.any((item) {
      if (item is! Map) {
        return false;
      }
      return item['name'] == 'prompt_studio' &&
          item['status'] == 'available' &&
          item['frontend_exposed'] == true;
    });
  }

  bool _contextAssemblerAvailable() {
    return _status.state.capabilities.any((item) {
      if (item is! Map) {
        return false;
      }
      return item['name'] == 'context_assembler' &&
          item['status'] == 'available' &&
          item['frontend_exposed'] == true;
    });
  }

  bool _writingWorkspaceAvailable() {
    return _status.state.capabilities.any((item) {
      if (item is! Map) {
        return false;
      }
      return item['name'] == 'writing_workspace' &&
          item['status'] == 'available' &&
          item['frontend_exposed'] == true;
    });
  }

  bool _revisionSystemAvailable() {
    return _status.state.capabilities.any((item) {
      if (item is! Map) {
        return false;
      }
      return item['name'] == 'revision_system' &&
          item['status'] == 'available' &&
          item['frontend_exposed'] == true;
    });
  }

  bool _datasetBuilderAvailable() {
    return _status.state.capabilities.any((item) {
      if (item is! Map) {
        return false;
      }
      return item['name'] == 'dataset_builder' &&
          item['status'] == 'available' &&
          item['frontend_exposed'] == true;
    });
  }

  bool _finetuneCenterAvailable() {
    return _status.state.capabilities.any((item) {
      if (item is! Map) {
        return false;
      }
      return item['name'] == 'finetune_center' &&
          item['status'] == 'available' &&
          item['frontend_exposed'] == true;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (!_shell.initialSetupCheckDone && widget.autoRefresh) {
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
                      _backend.backendStatus,
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

    if (_shell.requiresSetup) {
      return SetupPage(
        passwordController: _shell.setupPasswordController,
        confirmController: _shell.setupConfirmController,
        loading: _shell.loading,
        error: _shell.error,
        onInitialize: _initializeSetup,
        backendStatus: _backend.backendStatus,
      );
    }

    final pages = [
      StatusPage(
        runtime: _status.state.runtime,
        models: _models.models,
        gpuScheduler: _status.state.gpuScheduler,
        jobs: _jobs.state.jobs,
        capabilities: _status.state.capabilities,
        onCancelJob: _cancelJob,
      ),
      ModelsPage(
        models: _models.models,
        currentModel: _models.currentModel,
        selectedModelId: _models.selectedModelId,
        onRefresh: _refreshAll,
        onScan: _scanModels,
        onLoad: _loadModel,
        onUnload: _unloadModel,
        onSelect: _selectModel,
        onRegisterExternal: () =>
            _shell.setError('外部模型注册入口将在后续 UI 迭代中接入，请先使用后端 API 注册。'),
        onMoveToTrash: _deleteModel,
      ),
      ChatPage(
        controller: _chat,
        inputController: _chatInputController,
        systemController: _systemController,
        selectedModelId: _models.selectedModelId,
        currentModel: _models.currentModel,
        onSend: _sendChat,
        onStop: _chat.stop,
        onClear: _chat.clear,
        onRegenerate: _regenerateChat,
        onStreamingChanged: (value) async {
          _chat.streamingEnabled = value;
          await _savePreferences();
        },
      ),
      DownloadsPage(
        downloads: _downloads.state.downloads,
        repoController: _downloadRepoController,
        provider: _downloadProvider,
        revisionController: _downloadRevisionController,
        allowPatternsController: _downloadAllowController,
        ignorePatternsController: _downloadIgnoreController,
        onStart: _startDownload,
        onProviderChanged: (value) => setState(() => _downloadProvider = value),
        onCancel: _cancelDownload,
        onRetry: _retryDownload,
        onDelete: _deleteDownloadRecord,
        onViewModel: _viewDownloadedModel,
        onRefresh: _refreshAll,
      ),
      RagPage(
        queryController: _rag.queryController,
        result: _rag.state.result,
        onQuery: _queryRag,
      ),
      AdaptersPage(
        adapters: _adapters.state.adapters,
        currentModel: _models.currentModel,
        hasModelContext: _activeModelId().isNotEmpty,
        onRefresh: _refreshAll,
        onScan: _scanAdapters,
        onLoad: (id) =>
            _adapterAction((modelId) => _adapters.load(id, modelId)),
        onActivate: (id) =>
            _adapterAction((modelId) => _adapters.activate(id, modelId)),
        onDeactivate: (id) =>
            _adapterAction((modelId) => _adapters.deactivate(id, modelId)),
      ),
      BenchmarksPage(
        benchmarks: _benchmarks.state.benchmarks,
        currentModel: _models.currentModel,
        onStart: _startBenchmark,
        onRefresh: _refreshAll,
      ),
      StoragePage(
        storage: _storage.state.storage,
        cleanupPreview: _storage.state.cleanupPreview,
        onRefresh: _refreshAll,
        onPreview: _previewCleanup,
        onCleanup: _cleanupStorage,
      ),
      DiagnosticsPage(
        runtime: _status.state.runtime,
        capabilities: _status.state.capabilities,
        exportResult: _diagnostics.state.exportResult,
        onExport: _exportDiagnostics,
      ),
      NovelProjectsPage(controller: _novels),
      PromptStudioPage(controller: _prompts),
      ContextAssemblerPage(controller: _contextAssembler),
      WritingWorkspacePage(
        controller: _writing,
        onOpenRevision: (revisionId) {
          unawaited(_revisions.openRevision(revisionId));
          _navigation.select(revisionReviewPageIndex);
        },
      ),
      RevisionReviewPage(
        controller: _revisions,
        datasetController: _datasets,
        onOpenDatasetSample: (sampleId) {
          _navigation.select(datasetBuilderPageIndex);
        },
      ),
      DatasetBuilderPage(controller: _datasets),
      FinetuneCenterPage(
        controller: _finetune,
        onOpenAdapter: () {
          _navigation.select(5);
        },
      ),
      SettingsPage(
        apiBaseController: _settings.apiBaseController,
        userIdController: _settings.userIdController,
        apiKeyController: _settings.apiKeyController,
        localPythonController: _settings.localPythonController,
        localBackendRootController: _settings.localBackendRootController,
        backendMode: _settings.backendMode,
        autoStartBackend: _settings.autoStartBackend,
        closeBackendOnExit: _settings.closeBackendOnExit,
        backendLogs: _backend.recentLogs(),
        currentUser: _settings.currentUser,
        authUsers: _settings.authUsers,
        loadingAuthUsers: _settings.loadingAuthUsers,
        onApply: () async {
          _syncClientAuth();
          await _savePreferences();
          await _refreshAll();
        },
        onClearAuth: _clearAuth,
        onRestartBackend: _restartBackend,
        onStopBackend: _stopBackend,
        onLoadAuthUsers: _loadAuthUsers,
        onRegenerateApiKey: _regenerateApiKey,
        onBackendModeChanged: (value) async {
          _settings.setBackendMode(value);
          await _savePreferences();
        },
        onAutoStartChanged: (value) async {
          _settings.setAutoStartBackend(value);
          await _savePreferences();
        },
        onCloseOnExitChanged: (value) async {
          _settings.setCloseBackendOnExit(value);
          await _savePreferences();
        },
      ),
    ];

    return Scaffold(
      body: Row(
        children: [
          SizedBox(
            width: 188,
            child: buildShellNavigation(
              selectedIndex: _navigation.pageIndex,
              onSelected: _navigation.select,
              showNovelStudio: _novelStudioAvailable(),
              showPromptStudio: _promptStudioAvailable(),
              showContextAssembler: _contextAssemblerAvailable(),
              showWritingWorkspace: _writingWorkspaceAvailable(),
              showRevisionReview: _revisionSystemAvailable(),
              showDatasetBuilder: _datasetBuilderAvailable(),
              showFinetuneCenter: _finetuneCenterAvailable(),
            ),
          ),
          const VerticalDivider(width: 1),
          Expanded(
            child: Column(
              children: [
                TopBar(
                  loading: _shell.loading,
                  backendStatus: _backend.backendStatus,
                  modelLabel: _topModelLabel(),
                  adapterLabel: _topAdapterLabel(),
                  gpuLabel: _topGpuLabel(),
                  runningJobs: _runningJobCount(),
                  onRefresh: _refreshAll,
                ),
                if (_shell.authRequired)
                  MaterialBanner(
                    content: const Text(
                      '后端已经初始化，但当前客户端没有可用 API Key。请在 Settings 中填写 API Key，或重新生成 API Key。',
                    ),
                    leading: const Icon(Icons.lock_outline),
                    actions: [
                      TextButton(
                        onPressed: () => _navigation.select(settingsPageIndex),
                        child: const Text('打开 Settings'),
                      ),
                    ],
                  ),
                if (_shell.error != null)
                  MaterialBanner(
                    content: Text(_shell.error!),
                    leading: const Icon(Icons.error_outline),
                    actions: [
                      TextButton(
                        onPressed: _shell.clearError,
                        child: const Text('关闭'),
                      ),
                    ],
                  ),
                Expanded(child: pages[_navigation.pageIndex]),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
