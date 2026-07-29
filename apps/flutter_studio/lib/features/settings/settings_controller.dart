import 'package:flutter/widgets.dart';

import '../../core/config/app_settings_store.dart';

class SettingsController extends ChangeNotifier {
  SettingsController({AppSettingsStore? store})
    : _store = store ?? AppSettingsStore();

  final AppSettingsStore _store;

  final apiBaseController = TextEditingController(text: defaultApiBase);
  final userIdController = TextEditingController(text: 'admin');
  final apiKeyController = TextEditingController();
  final localPythonController = TextEditingController();
  final localBackendRootController = TextEditingController();

  bool autoStartBackend = true;
  bool closeBackendOnExit = true;
  String backendMode = 'local';
  String? selectedModelId;
  bool chatStreamingEnabled = true;

  Future<AppSettings> load() async {
    final settings = await _store.load();
    apiBaseController.text = settings.apiBaseUrl;
    userIdController.text = settings.userId;
    apiKeyController.text = settings.apiKey;
    localPythonController.text = settings.localPythonPath;
    localBackendRootController.text = settings.localBackendRoot;
    autoStartBackend = settings.autoStartBackend;
    closeBackendOnExit = settings.closeBackendOnExit;
    backendMode = settings.backendMode;
    selectedModelId = settings.selectedModelId;
    chatStreamingEnabled = settings.chatStreamingEnabled;
    notifyListeners();
    return settings;
  }

  Future<void> save({
    required String? selectedModelId,
    required bool chatStreamingEnabled,
  }) async {
    this.selectedModelId = selectedModelId;
    this.chatStreamingEnabled = chatStreamingEnabled;
    await _store.save(
      AppSettings(
        apiBaseUrl: apiBaseController.text.trim(),
        userId: userIdController.text.trim(),
        apiKey: apiKeyController.text.trim(),
        selectedModelId: selectedModelId,
        chatStreamingEnabled: chatStreamingEnabled,
        autoStartBackend: autoStartBackend,
        closeBackendOnExit: closeBackendOnExit,
        backendMode: backendMode,
        localPythonPath: localPythonController.text.trim(),
        localBackendRoot: localBackendRootController.text.trim(),
      ),
    );
    notifyListeners();
  }

  void setBackendMode(String value) {
    if (backendMode == value) {
      return;
    }
    backendMode = value;
    notifyListeners();
  }

  void setAutoStartBackend(bool value) {
    if (autoStartBackend == value) {
      return;
    }
    autoStartBackend = value;
    notifyListeners();
  }

  void setCloseBackendOnExit(bool value) {
    if (closeBackendOnExit == value) {
      return;
    }
    closeBackendOnExit = value;
    notifyListeners();
  }

  void clearApiKey() {
    apiKeyController.clear();
    notifyListeners();
  }

  @override
  void dispose() {
    apiBaseController.dispose();
    userIdController.dispose();
    apiKeyController.dispose();
    localPythonController.dispose();
    localBackendRootController.dispose();
    super.dispose();
  }
}
