class DiagnosticsState {
  const DiagnosticsState({
    this.exportResult,
    this.health,
    this.system,
    this.capabilities = const [],
    this.preview,
    this.loading = false,
    this.error,
  });

  final String? exportResult;
  final Map<String, dynamic>? health;
  final Map<String, dynamic>? system;
  final List<dynamic> capabilities;
  final Map<String, dynamic>? preview;
  final bool loading;
  final String? error;

  DiagnosticsState copyWith({
    String? exportResult,
    Map<String, dynamic>? health,
    Map<String, dynamic>? system,
    List<dynamic>? capabilities,
    Map<String, dynamic>? preview,
    bool? loading,
    String? error,
    bool clearExport = false,
    bool clearError = false,
  }) => DiagnosticsState(
    exportResult: clearExport ? null : exportResult ?? this.exportResult,
    health: health ?? this.health,
    system: system ?? this.system,
    capabilities: capabilities ?? this.capabilities,
    preview: preview ?? this.preview,
    loading: loading ?? this.loading,
    error: clearError ? null : error ?? this.error,
  );
}
