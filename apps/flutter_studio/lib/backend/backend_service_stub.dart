import 'backend_contract.dart';

BackendService createBackendService() => _UnsupportedBackendService();

class _UnsupportedBackendService implements BackendService {
  @override
  Future<BackendLaunchResult> ensureStarted({required String apiBase}) async {
    return const BackendLaunchResult(
      startedByApp: false,
      message: 'Automatic backend startup is only available on desktop.',
    );
  }

  @override
  Future<void> stop() async {}
}
