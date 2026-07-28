import 'package:shared_preferences/shared_preferences.dart';

const defaultApiBase = String.fromEnvironment(
  'LLM_STUDIO_API_BASE',
  defaultValue: 'http://127.0.0.1:8000',
);

class AppSettings {
  const AppSettings({
    required this.apiBaseUrl,
    required this.userId,
    required this.apiKey,
    required this.selectedModelId,
    required this.chatStreamingEnabled,
    required this.autoStartBackend,
    required this.closeBackendOnExit,
    required this.backendMode,
    required this.localPythonPath,
    required this.localBackendRoot,
  });

  factory AppSettings.defaults() => const AppSettings(
        apiBaseUrl: defaultApiBase,
        userId: 'admin',
        apiKey: '',
        selectedModelId: null,
        chatStreamingEnabled: true,
        autoStartBackend: true,
        closeBackendOnExit: true,
        backendMode: 'local',
        localPythonPath: '',
        localBackendRoot: '',
      );

  final String apiBaseUrl;
  final String userId;
  final String apiKey;
  final String? selectedModelId;
  final bool chatStreamingEnabled;
  final bool autoStartBackend;
  final bool closeBackendOnExit;
  final String backendMode;
  final String localPythonPath;
  final String localBackendRoot;
}

class AppSettingsStore {
  Future<AppSettings> load() async {
    final prefs = await SharedPreferences.getInstance();
    final defaults = AppSettings.defaults();
    return AppSettings(
      apiBaseUrl: prefs.getString('llm_studio.api_base_url') ?? defaults.apiBaseUrl,
      userId: prefs.getString('llm_studio.user_id') ?? defaults.userId,
      apiKey: prefs.getString('llm_studio.api_key') ?? defaults.apiKey,
      selectedModelId: prefs.getString('llm_studio.selected_model_id'),
      chatStreamingEnabled: prefs.getBool('llm_studio.chat_streaming_enabled') ?? defaults.chatStreamingEnabled,
      autoStartBackend: prefs.getBool('llm_studio.auto_start_backend') ?? defaults.autoStartBackend,
      closeBackendOnExit: prefs.getBool('llm_studio.close_backend_on_exit') ?? defaults.closeBackendOnExit,
      backendMode: prefs.getString('llm_studio.backend_mode') ?? defaults.backendMode,
      localPythonPath: prefs.getString('llm_studio.local_python_path') ?? defaults.localPythonPath,
      localBackendRoot: prefs.getString('llm_studio.local_backend_root') ?? defaults.localBackendRoot,
    );
  }

  Future<void> save(AppSettings settings) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('llm_studio.api_base_url', settings.apiBaseUrl);
    await prefs.setString('llm_studio.user_id', settings.userId);
    await prefs.setString('llm_studio.api_key', settings.apiKey);
    if (settings.selectedModelId == null || settings.selectedModelId!.isEmpty) {
      await prefs.remove('llm_studio.selected_model_id');
    } else {
      await prefs.setString('llm_studio.selected_model_id', settings.selectedModelId!);
    }
    await prefs.setBool('llm_studio.chat_streaming_enabled', settings.chatStreamingEnabled);
    await prefs.setBool('llm_studio.auto_start_backend', settings.autoStartBackend);
    await prefs.setBool('llm_studio.close_backend_on_exit', settings.closeBackendOnExit);
    await prefs.setString('llm_studio.backend_mode', settings.backendMode);
    await prefs.setString('llm_studio.local_python_path', settings.localPythonPath);
    await prefs.setString('llm_studio.local_backend_root', settings.localBackendRoot);
  }
}
