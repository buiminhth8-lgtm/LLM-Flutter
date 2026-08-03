import 'dart:convert';

import 'package:flutter/foundation.dart';

import '../../core/api/api_client.dart';
import 'diagnostics_state.dart';

class DiagnosticsController extends ChangeNotifier {
  DiagnosticsController(this._client);

  final LlmStudioClient _client;
  DiagnosticsState state = const DiagnosticsState();

  Future<void> refresh() async {
    state = state.copyWith(loading: true, clearError: true);
    notifyListeners();
    try {
      final results = await Future.wait<dynamic>([
        _client.diagnosticsHealth(),
        _client.diagnosticsSystem(),
        _client.diagnosticsCapabilities(),
        _client.diagnosticsPreview(),
      ]);
      state = state.copyWith(
        loading: false,
        health: results[0] as Map<String, dynamic>,
        system: results[1] as Map<String, dynamic>,
        capabilities: results[2] as List<dynamic>,
        preview: results[3] as Map<String, dynamic>,
        clearError: true,
      );
    } catch (error) {
      state = state.copyWith(loading: false, error: error.toString());
    }
    notifyListeners();
  }

  Future<void> export() async {
    state = state.copyWith(loading: true, clearError: true);
    notifyListeners();
    try {
      final result = await _client.exportDiagnostics();
      state = state.copyWith(
        loading: false,
        exportResult: const JsonEncoder.withIndent('  ').convert(result),
        clearError: true,
      );
    } catch (error) {
      state = state.copyWith(loading: false, error: error.toString());
      rethrow;
    }
    notifyListeners();
  }
}
