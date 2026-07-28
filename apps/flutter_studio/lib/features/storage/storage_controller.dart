import 'package:flutter/foundation.dart';

import '../../core/api/api_client.dart';
import 'storage_state.dart';

class StorageController extends ChangeNotifier {
  StorageController(this._client);

  final LlmStudioClient _client;
  StorageState state = const StorageState();

  Future<void> refresh() async {
    state = StorageState(
      storage: await _client.storage(),
      cleanupPreview: state.cleanupPreview,
    );
    notifyListeners();
  }

  Future<void> previewCleanup() async {
    state = StorageState(
      storage: state.storage,
      cleanupPreview: await _client.cleanupPreview(),
    );
    notifyListeners();
  }

  Future<void> cleanup() async {
    await _client.cleanupStorage();
    state = const StorageState();
    notifyListeners();
    await refresh();
  }
}
