class StatusState {
  const StatusState({
    this.runtime,
    this.gpuScheduler,
    this.capabilities = const [],
  });

  final Map<String, dynamic>? runtime;
  final Map<String, dynamic>? gpuScheduler;
  final List<dynamic> capabilities;
}
