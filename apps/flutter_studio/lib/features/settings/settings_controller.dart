import 'package:flutter/widgets.dart';

import '../../core/api/api_client.dart';
import '../../core/config/app_settings_store.dart';
import '../../core/models/dto.dart';

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
  AuthUserDto? currentUser;
  List<AuthUserDto> authUsers = const [];
  bool loadingAuthUsers = false;
  String? authManagementError;

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
    currentUser = null;
    authUsers = const [];
    notifyListeners();
  }

  Future<void> refreshCurrentUser(LlmStudioClient client) async {
    if (apiKeyController.text.trim().isEmpty) {
      currentUser = null;
      notifyListeners();
      return;
    }
    currentUser = await client.currentAuthUser();
    if (userIdController.text.trim().isEmpty && currentUser != null) {
      userIdController.text = currentUser!.userId;
    }
    notifyListeners();
  }

  Future<void> loadAuthUsers(LlmStudioClient client) async {
    loadingAuthUsers = true;
    authManagementError = null;
    notifyListeners();
    try {
      authUsers = await client.authUsers();
    } catch (error) {
      authManagementError = error.toString();
      rethrow;
    } finally {
      loadingAuthUsers = false;
      notifyListeners();
    }
  }

  Future<RegeneratedApiKeyDto> regenerateApiKey(
    LlmStudioClient client,
    String userId,
  ) async {
    final result = await client.regenerateApiKey(userId);
    authUsers = authUsers
        .map(
          (user) => user.userId == userId
              ? AuthUserDto(
                  userId: user.userId,
                  role: user.role,
                  enabled: user.enabled,
                  apiKeyMasked: result.apiKeyMasked,
                  note: user.note,
                  createdAt: user.createdAt,
                  updatedAt: user.updatedAt,
                )
              : user,
        )
        .toList();
    notifyListeners();
    return result;
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
