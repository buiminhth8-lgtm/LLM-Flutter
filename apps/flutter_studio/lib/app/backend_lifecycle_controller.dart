import 'dart:async';

import 'package:flutter/foundation.dart';

import '../core/backend/backend_service.dart';

class BackendLifecycleController extends ChangeNotifier {
  BackendLifecycleController({BackendService? backend})
    : _backend = backend ?? createBackendService();

  final BackendService _backend;
  String _backendStatus = '后端尚未启动。';

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
      _setBackendStatus('正在使用远程后端。');
      return;
    }
    _setBackendStatus('正在启动后端...');
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
    _setBackendStatus('Flutter 已停止后端。');
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
