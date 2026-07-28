import 'backend_contract.dart';

BackendService createBackendService() => _UnsupportedBackendService();

class _UnsupportedBackendService implements BackendService {
  @override
  Future<BackendLaunchResult> ensureStarted({
    required String apiBase,
    String localPythonPath = '',
    String localBackendRoot = '',
  }) async {
    return const BackendLaunchResult(
      startedByApp: false,
      message: 'Automatic backend startup is only available on desktop.',
    );
  }

  @override
  List<String> recentLogs({int limit = 200}) => const [];

  @override
  Future<void> stop() async {}
}
