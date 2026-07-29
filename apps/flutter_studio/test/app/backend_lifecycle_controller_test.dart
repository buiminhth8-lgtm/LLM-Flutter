import 'package:flutter_studio/app/backend_lifecycle_controller.dart';
import 'package:flutter_studio/core/backend/backend_contract.dart';
import 'package:flutter_test/flutter_test.dart';

class FakeBackendService implements BackendService {
  int ensureCalls = 0;
  int stopCalls = 0;

  @override
  Future<BackendLaunchResult> ensureStarted({
    required String apiBase,
    String localPythonPath = '',
    String localBackendRoot = '',
  }) async {
    ensureCalls += 1;
    return const BackendLaunchResult(startedByApp: true, message: 'started');
  }

  @override
  List<String> recentLogs({int limit = 200}) => const ['line1', 'line2'];

  @override
  Future<void> stop() async {
    stopCalls += 1;
  }
}

void main() {
  test('ensureStarted starts local backend when enabled', () async {
    final service = FakeBackendService();
    final controller = BackendLifecycleController(backend: service);

    await controller.ensureStarted(
      apiBase: 'http://127.0.0.1:8000',
      localMode: true,
      autoStart: true,
    );

    expect(service.ensureCalls, 1);
    expect(controller.backendStatus, 'started');
    expect(controller.recentLogs(), contains('line1'));
  });

  test('ensureStarted skips startup for remote backend', () async {
    final service = FakeBackendService();
    final controller = BackendLifecycleController(backend: service);

    await controller.ensureStarted(
      apiBase: 'http://127.0.0.1:8000',
      localMode: false,
      autoStart: true,
    );

    expect(service.ensureCalls, 0);
    expect(controller.backendStatus, 'Using remote backend.');
  });

  test('restart and stop delegate to backend service', () async {
    final service = FakeBackendService();
    final controller = BackendLifecycleController(backend: service);

    await controller.restart(apiBase: 'http://127.0.0.1:8000');
    await controller.stop();

    expect(service.stopCalls, 2);
    expect(service.ensureCalls, 1);
    expect(controller.backendStatus, 'Backend stopped by Flutter.');
  });
}
