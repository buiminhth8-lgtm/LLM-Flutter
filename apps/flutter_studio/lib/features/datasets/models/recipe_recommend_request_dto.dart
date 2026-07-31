class RecipeRecommendRequestDto {
  const RecipeRecommendRequestDto({
    this.baseModelId,
    this.method = 'qlora',
    this.gpuVramGb = 8,
    this.cudaAvailable = true,
    this.quality = 'balanced',
    this.maxSeqLength = 4096,
  });

  final String? baseModelId;
  final String method;
  final double gpuVramGb;
  final bool cudaAvailable;
  final String quality;
  final int maxSeqLength;

  Map<String, Object?> toMap() => {
    if (baseModelId != null) 'base_model_id': baseModelId,
    'method': method,
    'hardware': {'gpu_vram_gb': gpuVramGb, 'cuda_available': cudaAvailable},
    'preferences': {'quality': quality, 'max_seq_length': maxSeqLength},
  };
}
