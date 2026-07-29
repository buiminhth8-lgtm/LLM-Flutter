import 'dart:async';

import 'package:flutter/foundation.dart';

import '../core/backend/backend_service.dart';

class BackendLifecycleController extends ChangeNotifier {
  BackendLifecycleController({BackendService? backend})
    : _backend = backend ?? createBackendService();

  final BackendService _backend;
  String _backendStatus = 'Backend has not started yet.';

  String get backendStatus => _backendStatus;

  List<String> recentLogs({int limit = 200}) =>
      _backend.recentLogs(limit: limit);

  Future<void> ensureStarted({
    required String apiBase,
    required bool localMode,
    required bool autoStart,
    String localPythonPath = '',
    String localBackendRoot = '',
  }) async {
    if (!localMode || !autoStart) {
      _setBackendStatus('Using remote backend.');
      return;
    }
    _setBackendStatus('Starting backend...');
    final result = await _backend.ensureStarted(
      apiBase: apiBase,
      localPythonPath: localPythonPath,
      localBackendRoot: localBackendRoot,
    );
    _setBackendStatus(result.message);
  }

  Future<void> restart({
    required String apiBase,
    String localPythonPath = '',
    String localBackendRoot = '',
  }) async {
    await _backend.stop();
    final result = await _backend.ensureStarted(
      apiBase: apiBase,
      localPythonPath: localPythonPath,
      localBackendRoot: localBackendRoot,
    );
    _setBackendStatus(result.message);
  }

  Future<void> stop() async {
    await _backend.stop();
    _setBackendStatus('Backend stopped by Flutter.');
  }

  Future<void> stopIfConfigured(bool closeOnExit) async {
    if (closeOnExit) {
      await _backend.stop();
    }
  }

  void _setBackendStatus(String value) {
    if (_backendStatus == value) {
      return;
    }
    _backendStatus = value;
    notifyListeners();
  }
}
