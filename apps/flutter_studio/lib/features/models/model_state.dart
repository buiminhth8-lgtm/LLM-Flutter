class ModelState {
  const ModelState({
    this.models = const [],
    this.currentModel,
    this.selectedModelId,
  });

  final List<dynamic> models;
  final Map<String, dynamic>? currentModel;
  final String? selectedModelId;

  ModelState copyWith({
    List<dynamic>? models,
    Map<String, dynamic>? currentModel,
    String? selectedModelId,
    bool clearSelectedModel = false,
  }) {
    return ModelState(
      models: models ?? this.models,
      currentModel: currentModel ?? this.currentModel,
      selectedModelId: clearSelectedModel
          ? null
          : selectedModelId ?? this.selectedModelId,
    );
  }
}
