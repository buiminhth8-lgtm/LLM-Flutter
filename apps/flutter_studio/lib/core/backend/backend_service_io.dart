import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

import 'backend_contract.dart';

const _configuredProjectRoot = String.fromEnvironment('LLM_STUDIO_ROOT');
const _configuredPythonExecutable = String.fromEnvironment('LLM_STUDIO_PYTHON');

BackendService createBackendService() => DesktopBackendService();

class DesktopBackendService implements BackendService {
  Process? _process;
  bool _startedByApp = false;
  final List<String> _logs = <String>[];

  @override
  Future<BackendLaunchResult> ensureStarted({
    required String apiBase,
    String localPythonPath = '',
    String localBackendRoot = '',
  }) async {
    if (await _isHealthy(apiBase)) {
      return const BackendLaunchResult(startedByApp: false, message: '后端已在运行。');
    }

    final root = _findProjectRoot(localBackendRoot);
    final python = await _resolvePython(root, localPythonPath);

    final uri = Uri.parse(apiBase);
    final host = uri.host.isEmpty ? '127.0.0.1' : uri.host;
    final port = uri.hasPort ? uri.port.toString() : '8000';

    _process = await Process.start(
      python.executable,
      buildBackendServiceArgumentsForTesting(
        host: host,
        port: port,
        pythonPrefix: python.arguments,
      ),
      workingDirectory: root.path,
      mode: ProcessStartMode.normal,
    );
    _startedByApp = true;
    _drain(_process!.stdout, 'stdout');
    _drain(_process!.stderr, 'stderr');
    var exited = false;
    unawaited(_process!.exitCode.then((_) => exited = true));

    for (var attempt = 0; attempt < 60; attempt += 1) {
      if (await _isHealthy(apiBase)) {
        return const BackendLaunchResult(
          startedByApp: true,
          message: 'Flutter 已启动后端。',
        );
      }
      if (exited) {
        throw StateError(
          '后端进程在健康检查通过前已退出。\n'
          '${recentLogs(limit: 20).join('\n')}',
        );
      }
      await Future<void>.delayed(const Duration(seconds: 1));
    }

    throw TimeoutException('后端启动超时。\n${recentLogs(limit: 20).join('\n')}');
  }

  @override
  List<String> recentLogs({int limit = 200}) {
    if (_logs.length <= limit) {
      return List<String>.unmodifiable(_logs);
    }
    return List<String>.unmodifiable(_logs.sublist(_logs.length - limit));
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

  Directory _findProjectRoot(String configuredRoot) {
    final candidates = <Directory>[
      if (configuredRoot.trim().isNotEmpty) Directory(configuredRoot.trim()),
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

    throw StateError('无法定位 LLM-Studio 项目根目录。请将 LLM_STUDIO_ROOT 设置为仓库目录。');
  }

  Future<_PythonCommand> _resolvePython(
    Directory root,
    String configuredPython,
  ) async {
    final candidates = <_PythonCommand>[
      if (configuredPython.trim().isNotEmpty)
        _PythonCommand(configuredPython.trim()),
      if (_configuredPythonExecutable.isNotEmpty)
        _PythonCommand(_configuredPythonExecutable),
      if ((Platform.environment['LLM_STUDIO_PYTHON'] ?? '').isNotEmpty)
        _PythonCommand(Platform.environment['LLM_STUDIO_PYTHON']!),
      _PythonCommand(
        '${root.path}${Platform.pathSeparator}.venv'
        '${Platform.pathSeparator}Scripts${Platform.pathSeparator}python.exe',
      ),
      _PythonCommand(
        '${root.path}${Platform.pathSeparator}venv'
        '${Platform.pathSeparator}Scripts${Platform.pathSeparator}python.exe',
      ),
      const _PythonCommand('python'),
      const _PythonCommand('py', arguments: ['-3.12']),
    ];

    final failures = <String>[];
    for (final candidate in candidates) {
      if (candidate.executable.contains(Platform.pathSeparator) &&
          !File(candidate.executable).existsSync()) {
        failures.add('${candidate.label}: 未找到可执行文件');
        continue;
      }
      final ok = await _verifyPython(candidate, root, failures);
      if (ok) {
        return candidate;
      }
    }

    throw StateError(
      'Could not find a Python environment that can import LLM-Studio and uvicorn.\n'
      '${failures.take(6).join('\n')}\n'
      '请运行：python -m pip install -e . 以及 python -m pip install -r requirements/web.txt',
    );
  }

  Future<bool> _verifyPython(
    _PythonCommand candidate,
    Directory root,
    List<String> failures,
  ) async {
    final probes = const [
      'import sys; print(sys.executable)',
      'import llm_studio; print(llm_studio.__file__)',
      'import uvicorn; print(uvicorn.__version__)',
    ];
    for (final probe in probes) {
      try {
        final result = await Process.run(candidate.executable, [
          ...candidate.arguments,
          '-c',
          probe,
        ], workingDirectory: root.path).timeout(const Duration(seconds: 8));
        final output = [
          if ((result.stdout as String).trim().isNotEmpty)
            (result.stdout as String).trim(),
          if ((result.stderr as String).trim().isNotEmpty)
            (result.stderr as String).trim(),
        ].join('\n');
        if (output.isNotEmpty) {
          _appendLog('[python-probe] ${_redactSecrets(output)}');
        }
        if (result.exitCode != 0) {
          failures.add('${candidate.label}: ${_redactSecrets(output)}');
          return false;
        }
      } catch (error) {
        failures.add('${candidate.label}: $error');
        return false;
      }
    }
    return true;
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

  void _drain(Stream<List<int>> stream, String source) {
    stream
        .transform(utf8.decoder)
        .transform(const LineSplitter())
        .listen((line) => _appendLog('[$source] ${_redactSecrets(line)}'));
  }

  void _appendLog(String line) {
    _logs.add(line);
    if (_logs.length > 200) {
      _logs.removeRange(0, _logs.length - 200);
    }
  }

  String _redactSecrets(String value) {
    var redacted = value.replaceAll(
      RegExp(r'Authorization:\s*Bearer\s+\S+', caseSensitive: false),
      'Authorization: Bearer <redacted>',
    );
    redacted = redacted.replaceAll(
      RegExp(r'X-API-Key:\s*\S+', caseSensitive: false),
      'X-API-Key: <redacted>',
    );
    redacted = redacted.replaceAll(
      RegExp(r'(api_key|password|cookie|token)=\S+', caseSensitive: false),
      r'$1=<redacted>',
    );
    return redacted;
  }
}

List<String> buildBackendServiceArgumentsForTesting({
  required String host,
  required String port,
  List<String> pythonPrefix = const [],
}) {
  return [
    ...pythonPrefix,
    '-m',
    'llm_studio.server',
    '--host',
    host,
    '--port',
    port,
  ];
}

String redactBackendLogForTesting(String value) {
  return DesktopBackendService()._redactSecrets(value);
}

class _PythonCommand {
  const _PythonCommand(this.executable, {this.arguments = const []});

  final String executable;
  final List<String> arguments;

  String get label => ([executable, ...arguments]).join(' ');
}
