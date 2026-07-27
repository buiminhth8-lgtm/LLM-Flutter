import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

import 'backend_contract.dart';

const _configuredProjectRoot = String.fromEnvironment('LLM_STUDIO_ROOT');
const _configuredPythonExecutable = String.fromEnvironment(
  'LLM_STUDIO_PYTHON',
);

BackendService createBackendService() => DesktopBackendService();

class DesktopBackendService implements BackendService {
  Process? _process;
  bool _startedByApp = false;

  @override
  Future<BackendLaunchResult> ensureStarted({required String apiBase}) async {
    if (await _isHealthy(apiBase)) {
      return const BackendLaunchResult(
        startedByApp: false,
        message: 'Backend is already running.',
      );
    }

    final root = _findProjectRoot();
    final python = _resolvePython(root);
    if (!python.existsSync()) {
      throw StateError(
        'Missing Python executable at ${python.path}. '
        'Run scripts/setup_windows_python312.ps1, or set LLM_STUDIO_PYTHON.',
      );
    }

    final uri = Uri.parse(apiBase);
    final host = uri.host.isEmpty ? '127.0.0.1' : uri.host;
    final port = uri.hasPort ? uri.port.toString() : '8000';

    _process = await Process.start(
      python.path,
      ['-m', 'llm_studio.cli', 'serve', '--host', host, '--port', port],
      workingDirectory: root.path,
      mode: ProcessStartMode.normal,
    );
    _startedByApp = true;
    _drain(_process!.stdout);
    _drain(_process!.stderr);
    var exited = false;
    unawaited(_process!.exitCode.then((_) => exited = true));

    for (var attempt = 0; attempt < 60; attempt += 1) {
      if (await _isHealthy(apiBase)) {
        return const BackendLaunchResult(
          startedByApp: true,
          message: 'Backend started by Flutter.',
        );
      }
      if (exited) {
        throw StateError('Backend process exited before becoming healthy.');
      }
      await Future<void>.delayed(const Duration(seconds: 1));
    }

    throw TimeoutException('Backend startup timed out.');
  }

  @override
  Future<void> stop() async {
    if (_startedByApp && _process != null) {
      _process!.kill();
      await _process!.exitCode.timeout(
        const Duration(seconds: 5),
        onTimeout: () => -1,
      );
    }
    _process = null;
    _startedByApp = false;
  }

  Future<bool> _isHealthy(String apiBase) async {
    try {
      final response = await http
          .get(Uri.parse('$apiBase/health'))
          .timeout(const Duration(seconds: 2));
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  Directory _findProjectRoot() {
    final candidates = <Directory>[
      if (_configuredProjectRoot.isNotEmpty) Directory(_configuredProjectRoot),
      if ((Platform.environment['LLM_STUDIO_ROOT'] ?? '').isNotEmpty)
        Directory(Platform.environment['LLM_STUDIO_ROOT']!),
      Directory.current,
      File(Platform.resolvedExecutable).parent,
    ];

    for (final candidate in candidates) {
      final found = _walkUp(candidate.absolute);
      if (found != null) {
        return found;
      }
    }

    throw StateError(
      'Could not locate LLM-Studio project root. '
      'Set LLM_STUDIO_ROOT to the repository directory.',
    );
  }

  File _resolvePython(Directory root) {
    if (_configuredPythonExecutable.isNotEmpty) {
      return File(_configuredPythonExecutable);
    }

    final envPython = Platform.environment['LLM_STUDIO_PYTHON'];
    if (envPython != null && envPython.isNotEmpty) {
      return File(envPython);
    }

    return File(
      '${root.path}${Platform.pathSeparator}.venv'
      '${Platform.pathSeparator}Scripts${Platform.pathSeparator}python.exe',
    );
  }

  Directory? _walkUp(Directory start) {
    var current = start;
    while (true) {
      final package = Directory(
        '${current.path}${Platform.pathSeparator}llm_studio',
      );
      final pyproject = File(
        '${current.path}${Platform.pathSeparator}pyproject.toml',
      );
      final config = File(
        '${current.path}${Platform.pathSeparator}config.yaml',
      );
      if (package.existsSync() &&
          (pyproject.existsSync() || config.existsSync())) {
        return current;
      }

      final parent = current.parent;
      if (parent.path == current.path) {
        return null;
      }
      current = parent;
    }
  }

  void _drain(Stream<List<int>> stream) {
    stream.transform(utf8.decoder).listen((_) {});
  }
}
