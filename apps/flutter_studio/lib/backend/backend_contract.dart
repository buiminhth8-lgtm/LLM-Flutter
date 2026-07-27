abstract interface class BackendService {
  Future<BackendLaunchResult> ensureStarted({required String apiBase});

  List<String> recentLogs({int limit = 200});

  Future<void> stop();
}

class BackendLaunchResult {
  const BackendLaunchResult({
    required this.startedByApp,
    required this.message,
  });

  final bool startedByApp;
  final String message;
}
