import 'package:flutter/foundation.dart';

import '../../core/api/api_client.dart';
import 'model_state.dart';

class ModelController extends ChangeNotifier {
  ModelController(this._client);

  final LlmStudioClient _client;
  ModelState state = const ModelState();

  List<dynamic> get models => state.models;
  Map<String, dynamic>? get currentModel => state.currentModel;
  String? get selectedModelId => state.selectedModelId;

  Future<void> refresh() async {
    final models = await _client.models();
    final currentModel = await _client.currentModel();
    var selected = state.selectedModelId;
    if (selected != null &&
        !models.any((model) => model is Map && model['id'] == selected)) {
      selected = null;
    }
    state = ModelState(
      models: models,
      currentModel: currentModel,
      selectedModelId: selected,
    );
    notifyListeners();
  }

  Future<void> scan() async {
    await _client.scanModels();
    await refresh();
  }

  Future<void> load(String modelId) async {
    final current = await _client.loadModel(modelId);
    state = state.copyWith(selectedModelId: '${current['model_id'] ?? modelId}');
    notifyListeners();
    await refresh();
  }

  Future<void> unload() async {
    final modelId = activeModelId();
    if (modelId.isEmpty) {
      return;
    }
    await _client.unloadModel(modelId);
    state = state.copyWith(clearSelectedModel: true);
    notifyListeners();
    await refresh();
  }

  Future<void> select(String modelId) async {
    state = state.copyWith(selectedModelId: modelId);
    notifyListeners();
  }

  Future<void> delete(String modelId) async {
    await _client.deleteModel(modelId, confirm: true);
    state = state.copyWith(
      clearSelectedModel: state.selectedModelId == modelId,
    );
    notifyListeners();
    await refresh();
  }

  void restoreSelectedModel(String? modelId) {
    state = state.copyWith(
      selectedModelId: modelId,
      clearSelectedModel: modelId == null || modelId.isEmpty,
    );
    notifyListeners();
  }

  void clear() {
    state = const ModelState();
    notifyListeners();
  }

  String activeModelId() {
    return state.selectedModelId ??
        (state.currentModel?['loaded'] == true
            ? '${state.currentModel?['model_id']}'
            : '');
  }
}
