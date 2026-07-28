import 'dart:convert';

import 'package:flutter/foundation.dart';

import '../../core/api/api_client.dart';
import 'diagnostics_state.dart';

class DiagnosticsController extends ChangeNotifier {
  DiagnosticsController(this._client);

  final LlmStudioClient _client;
  DiagnosticsState state = const DiagnosticsState();

  Future<void> export() async {
    final result = await _client.exportDiagnostics();
    state = DiagnosticsState(
      exportResult: const JsonEncoder.withIndent('  ').convert(result),
    );
    notifyListeners();
  }
}
