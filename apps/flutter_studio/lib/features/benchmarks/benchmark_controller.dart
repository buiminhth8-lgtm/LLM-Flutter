import 'package:flutter/foundation.dart';

import '../../core/api/api_client.dart';
import 'benchmark_state.dart';

class BenchmarkController extends ChangeNotifier {
  BenchmarkController(this._client);

  final LlmStudioClient _client;
  BenchmarkState state = const BenchmarkState();

  Future<void> refresh() async {
    state = BenchmarkState(benchmarks: await _client.benchmarks());
    notifyListeners();
  }

  Future<void> start(String modelId) async {
    await _client.startBenchmark(modelId: modelId);
    await refresh();
  }
}
