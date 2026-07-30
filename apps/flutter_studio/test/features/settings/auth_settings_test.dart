import 'package:flutter/material.dart';
import 'package:flutter_studio/core/models/dto.dart';
import 'package:flutter_studio/features/settings/settings_page.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('admin can see user management and recovery guide', (tester) async {
    await tester.binding.setSurfaceSize(const Size(1000, 1200));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    var loadCalled = false;
    var regenerateCalled = false;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SettingsPage(
            apiBaseController: TextEditingController(text: 'http://127.0.0.1:8000'),
            userIdController: TextEditingController(text: 'admin'),
            apiKeyController: TextEditingController(text: 'sk-admin'),
            localPythonController: TextEditingController(),
            localBackendRootController: TextEditingController(),
            backendMode: 'local',
            autoStartBackend: true,
            closeBackendOnExit: true,
            backendLogs: const [],
            currentUser: const AuthUserDto(userId: 'admin', role: 'admin', enabled: true),
            authUsers: const [
              AuthUserDto(
                userId: 'operator',
                role: 'operator',
                enabled: true,
                apiKeyMasked: 'sk-llmstudio...abcd',
              ),
            ],
            loadingAuthUsers: false,
            onApply: () {},
            onClearAuth: () {},
            onRestartBackend: () {},
            onStopBackend: () {},
            onLoadAuthUsers: () async {
              loadCalled = true;
            },
            onRegenerateApiKey: (userId) async {
              regenerateCalled = true;
              return const RegeneratedApiKeyDto(
                userId: 'operator',
                apiKey: 'sk-new',
                apiKeyMasked: 'sk...new',
              );
            },
            onBackendModeChanged: (_) {},
            onAutoStartChanged: (_) {},
            onCloseOnExitChanged: (_) {},
          ),
        ),
      ),
    );

    expect(find.text('Load users'), findsOneWidget);
    expect(find.text('Regenerate'), findsOneWidget);
    expect(find.text('python tools/reset_auth.py --reset-admin'), findsOneWidget);

    await tester.ensureVisible(find.text('Load users'));
    await tester.tap(find.text('Load users'));
    await tester.pump();
    expect(loadCalled, isTrue);

    await tester.ensureVisible(find.text('Regenerate'));
    await tester.tap(find.text('Regenerate'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Regenerate').last);
    await tester.pumpAndSettle();
    expect(regenerateCalled, isTrue);
    expect(find.text('New API Key'), findsOneWidget);
  });

  testWidgets('non-admin does not see regenerate controls', (tester) async {
    await tester.binding.setSurfaceSize(const Size(1000, 1000));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SettingsPage(
            apiBaseController: TextEditingController(text: 'http://127.0.0.1:8000'),
            userIdController: TextEditingController(),
            apiKeyController: TextEditingController(),
            localPythonController: TextEditingController(),
            localBackendRootController: TextEditingController(),
            backendMode: 'local',
            autoStartBackend: true,
            closeBackendOnExit: true,
            backendLogs: const [],
            currentUser: const AuthUserDto(userId: 'viewer', role: 'viewer', enabled: true),
            authUsers: const [],
            loadingAuthUsers: false,
            onApply: () {},
            onClearAuth: () {},
            onRestartBackend: () {},
            onStopBackend: () {},
            onLoadAuthUsers: () async {},
            onRegenerateApiKey: (_) async => const RegeneratedApiKeyDto(
              userId: 'viewer',
              apiKey: 'sk-new',
              apiKeyMasked: 'sk...new',
            ),
            onBackendModeChanged: (_) {},
            onAutoStartChanged: (_) {},
            onCloseOnExitChanged: (_) {},
          ),
        ),
      ),
    );

    expect(find.text('User Management 仅 admin 可见。'), findsOneWidget);
    expect(find.text('Regenerate'), findsNothing);
  });
}
