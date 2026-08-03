import 'finetune_preflight_dto.dart';

class FinetuneCreateRunRequestDto extends FinetunePreflightRequestDto {
  const FinetuneCreateRunRequestDto({
    required super.datasetVersionId,
    required super.recipeId,
    required super.baseModelId,
    required super.adapterName,
    this.startImmediately = true,
  });

  final bool startImmediately;

  @override
  Map<String, Object?> toMap() => {
    ...super.toMap(),
    'start_immediately': startImmediately,
  };
}
