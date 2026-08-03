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
      message: '自动启动后端仅支持桌面端。',
    );
  }

  @override
  List<String> recentLogs({int limit = 200}) => const [];

  @override
  Future<void> stop() async {}
}
