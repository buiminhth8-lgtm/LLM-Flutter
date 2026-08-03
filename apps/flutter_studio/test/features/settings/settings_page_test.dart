import 'package:flutter/material.dart';
import 'package:flutter_studio/features/settings/settings_page.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets(
    'Settings page exposes Stage 12 backend and diagnostics actions',
    (tester) async {
      var tested = false;
      var diagnostics = false;
      var releaseNotes = false;
      await tester.binding.setSurfaceSize(const Size(1200, 1000));
      addTearDown(() => tester.binding.setSurfaceSize(null));
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: SettingsPage(
              apiBaseController: TextEditingController(
                text: 'http://127.0.0.1:8000',
              ),
              userIdController: TextEditingController(),
              apiKeyController: TextEditingController(),
              localPythonController: TextEditingController(),
              localBackendRootController: TextEditingController(),
              backendMode: 'local',
              autoStartBackend: true,
              closeBackendOnExit: true,
              backendLogs: const [],
              currentUser: null,
              authUsers: const [],
              loadingAuthUsers: false,
              onApply: () {},
              onClearAuth: () {},
              onRestartBackend: () {},
              onStopBackend: () {},
              onLoadAuthUsers: () async {},
              onRegenerateApiKey: (_) async => throw UnimplementedError(),
              onBackendModeChanged: (_) {},
              onAutoStartChanged: (_) {},
              onCloseOnExitChanged: (_) {},
              onTestBackend: () => tested = true,
              onOpenDiagnostics: () => diagnostics = true,
              onOpenReleaseNotes: () => releaseNotes = true,
            ),
          ),
        ),
      );

      await tester.tap(find.text('Test backend'));
      await tester.tap(find.text('Diagnostics'));
      await tester.tap(find.text('Release notes'));

      expect(tested, isTrue);
      expect(diagnostics, isTrue);
      expect(releaseNotes, isTrue);
    },
  );
}
