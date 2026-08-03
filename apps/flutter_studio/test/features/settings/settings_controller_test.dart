import 'package:flutter_studio/features/settings/settings_controller.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test(
    'load restores settings and clearApiKey clears only the API key field',
    () async {
      SharedPreferences.setMockInitialValues({
        'llm_studio.api_base_url': 'http://localhost:9000',
        'llm_studio.user_id': 'operator',
        'llm_studio.api_key': 'secret-key',
        'llm_studio.auto_start_backend': false,
        'llm_studio.close_backend_on_exit': false,
        'llm_studio.backend_mode': 'remote',
        'llm_studio.local_python_path': r'C:\Python312\python.exe',
        'llm_studio.local_backend_root': r'D:\repo',
      });
      final controller = SettingsController();

      await controller.load();
      controller.clearApiKey();

      expect(controller.apiBaseController.text, 'http://localhost:9000');
      expect(controller.userIdController.text, 'operator');
      expect(controller.apiKeyController.text, isEmpty);
      expect(controller.autoStartBackend, isFalse);
      expect(controller.closeBackendOnExit, isFalse);
      expect(controller.backendMode, 'remote');
    },
  );

  test('save persists changed backend and auth settings', () async {
    SharedPreferences.setMockInitialValues({});
    final controller = SettingsController();
    controller.apiBaseController.text = 'http://127.0.0.1:8001';
    controller.userIdController.text = 'admin';
    controller.apiKeyController.text = 'key';
    controller.setBackendMode('remote');
    controller.setAutoStartBackend(false);

    await controller.save(
      selectedModelId: 'model-a',
      chatStreamingEnabled: false,
    );

    final prefs = await SharedPreferences.getInstance();
    expect(prefs.getString('llm_studio.api_base_url'), 'http://127.0.0.1:8001');
    expect(prefs.getString('llm_studio.api_key'), 'key');
    expect(prefs.getString('llm_studio.selected_model_id'), 'model-a');
    expect(prefs.getBool('llm_studio.chat_streaming_enabled'), isFalse);
    expect(prefs.getBool('llm_studio.auto_start_backend'), isFalse);
    expect(prefs.getString('llm_studio.backend_mode'), 'remote');
  });

  test('save allows empty user id for bearer-only authentication', () async {
    SharedPreferences.setMockInitialValues({});
    final controller = SettingsController();
    controller.userIdController.text = '';
    controller.apiKeyController.text = 'bearer-only-key';

    await controller.save(selectedModelId: null, chatStreamingEnabled: true);

    final prefs = await SharedPreferences.getInstance();
    expect(prefs.getString('llm_studio.user_id'), '');
    expect(prefs.getString('llm_studio.api_key'), 'bearer-only-key');
  });
}
