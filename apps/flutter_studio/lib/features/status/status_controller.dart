import 'package:flutter/foundation.dart';

import '../../core/api/api_client.dart';
import 'status_state.dart';

class StatusController extends ChangeNotifier {
  StatusController(this._client);

  final LlmStudioClient _client;
  StatusState state = const StatusState();

  Future<void> refresh() async {
    final results = await Future.wait<dynamic>([
      _client.runtime(),
      _client.gpuScheduler(),
      _client.capabilities(),
    ]);
    state = StatusState(
      runtime: results[0] as Map<String, dynamic>,
      gpuScheduler: results[1] as Map<String, dynamic>,
      capabilities: results[2] as List<dynamic>,
    );
    notifyListeners();
  }

  void clear() {
    state = const StatusState();
    notifyListeners();
  }
}
