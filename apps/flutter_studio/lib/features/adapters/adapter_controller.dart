import 'package:flutter/foundation.dart';

import '../../core/api/api_client.dart';
import 'adapter_state.dart';

class AdapterController extends ChangeNotifier {
  AdapterController(this._client);

  final LlmStudioClient _client;
  AdapterState state = const AdapterState();

  Future<void> refresh() async {
    state = AdapterState(adapters: await _client.adapters());
    notifyListeners();
  }

  Future<void> scan() async {
    await _client.scanAdapters();
    await refresh();
  }

  Future<void> load(String id, String modelId) async {
    await _client.loadAdapter(id, modelId);
    await refresh();
  }

  Future<void> activate(String id, String modelId) async {
    await _client.activateAdapter(id, modelId);
    await refresh();
  }

  Future<void> deactivate(String id, String modelId) async {
    await _client.deactivateAdapter(id, modelId: modelId);
    await refresh();
  }
}
