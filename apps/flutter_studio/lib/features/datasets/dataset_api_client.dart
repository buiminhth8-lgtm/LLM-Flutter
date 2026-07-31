import '../../core/api/api_client.dart';
import 'models/dataset_export_dto.dart';
import 'models/dataset_freeze_request_dto.dart';
import 'models/dataset_manifest_dto.dart';
import 'models/dataset_version_dto.dart';
import 'models/dataset_version_sample_dto.dart';
import 'models/recipe_recommend_request_dto.dart';
import 'models/training_recipe_dto.dart';
import 'models/training_dataset_dto.dart';
import 'models/training_sample_dto.dart';

class DatasetApiClient {
  DatasetApiClient(this._client);

  final LlmStudioClient _client;

  Future<TrainingDatasetDto> createDataset(CreateDatasetRequest request) async {
    final body = await _client.createDataset(request.toMap());
    return TrainingDatasetDto.fromMap(body);
  }

  Future<List<TrainingDatasetDto>> listDatasets({
    String? projectId,
    String? type,
    String? status,
  }) async {
    final items = await _client.datasets(
      projectId: projectId,
      type: type,
      status: status,
    );
    return items
        .whereType<Map>()
        .map(TrainingDatasetDto.fromMap)
        .toList(growable: false);
  }

  Future<TrainingDatasetDto> getDataset(String datasetId) async {
    final body = await _client.dataset(datasetId);
    return TrainingDatasetDto.fromMap(body);
  }

  Future<TrainingSampleDto> createSampleFromRevision({
    required String datasetId,
    required String revisionId,
    String sampleType = 'sft',
  }) async {
    final body = await _client.createDatasetSampleFromRevision(datasetId, {
      'revision_id': revisionId,
      'sample_type': sampleType,
    });
    return TrainingSampleDto.fromMap(body);
  }

  Future<BulkCreateSamplesResultDto> bulkCreateSamplesFromRevisions({
    required String datasetId,
    String? projectId,
    String? chapterId,
    int? minScore,
    List<String>? tags,
    String sampleType = 'sft',
  }) async {
    final request = <String, Object?>{
      'accepted_for_dataset': true,
      'revision_status': 'approved',
      'sample_type': sampleType,
    };
    if (projectId != null) {
      request['project_id'] = projectId;
    }
    if (chapterId != null) {
      request['chapter_id'] = chapterId;
    }
    if (minScore != null) {
      request['min_score'] = minScore;
    }
    if (tags != null) {
      request['tags'] = tags;
    }
    final body = await _client.bulkCreateDatasetSamplesFromRevisions(
      datasetId,
      request,
    );
    return BulkCreateSamplesResultDto.fromMap(body);
  }

  Future<List<TrainingSampleDto>> listSamples({
    required String datasetId,
    String? status,
    String? sampleType,
  }) async {
    final items = await _client.datasetSamples(
      datasetId,
      status: status,
      sampleType: sampleType,
    );
    return items
        .whereType<Map>()
        .map(TrainingSampleDto.fromMap)
        .toList(growable: false);
  }

  Future<TrainingSampleDto> getSample(String sampleId) async {
    final body = await _client.datasetSample(sampleId);
    return TrainingSampleDto.fromMap(body);
  }

  Future<TrainingSampleDto> updateSample(
    String sampleId,
    UpdateSampleRequest request,
  ) async {
    final body = await _client.updateDatasetSample(sampleId, request.toMap());
    return TrainingSampleDto.fromMap(body);
  }

  Future<TrainingSampleDto> approveSample(String sampleId) async {
    final body = await _client.approveDatasetSample(sampleId);
    return TrainingSampleDto.fromMap(body);
  }

  Future<TrainingSampleDto> rejectSample(
    String sampleId, {
    String? reason,
  }) async {
    final body = await _client.rejectDatasetSample(sampleId, reason: reason);
    return TrainingSampleDto.fromMap(body);
  }

  Future<DatasetExportDto> exportDataset({
    required String datasetId,
    String format = 'sft_jsonl',
    bool approvedOnly = true,
    String? fileName,
  }) async {
    final request = <String, Object?>{
      'format': format,
      'approved_only': approvedOnly,
    };
    if (fileName != null) {
      request['file_name'] = fileName;
    }
    final body = await _client.exportDataset(datasetId, request);
    return DatasetExportDto.fromMap(body);
  }

  Future<List<DatasetExportDto>> listExports(String datasetId) async {
    final items = await _client.datasetExports(datasetId);
    return items
        .whereType<Map>()
        .map(DatasetExportDto.fromMap)
        .toList(growable: false);
  }

  Future<TrainingDatasetDto> markReady(String datasetId) async {
    final body = await _client.markDatasetReady(datasetId);
    return TrainingDatasetDto.fromMap(body);
  }

  Future<TrainingDatasetDto> markDirty(String datasetId) async {
    final body = await _client.markDatasetDirty(datasetId);
    return TrainingDatasetDto.fromMap(body);
  }

  Future<DatasetVersionDto> freezeDataset({
    required String datasetId,
    required DatasetFreezeRequestDto request,
  }) async {
    final body = await _client.freezeDatasetVersion(datasetId, request.toMap());
    return DatasetVersionDto.fromMap(body);
  }

  Future<List<DatasetVersionDto>> listVersions(String datasetId) async {
    final items = await _client.datasetVersions(datasetId);
    return items
        .whereType<Map>()
        .map(DatasetVersionDto.fromMap)
        .toList(growable: false);
  }

  Future<DatasetVersionDto> getVersion(String datasetVersionId) async {
    final body = await _client.datasetVersion(datasetVersionId);
    return DatasetVersionDto.fromMap(body);
  }

  Future<DatasetManifestDto> getManifest(String datasetVersionId) async {
    final body = await _client.datasetVersionManifest(datasetVersionId);
    return DatasetManifestDto.fromMap(body);
  }

  Future<List<DatasetVersionSampleDto>> listVersionSamples(
    String datasetVersionId, {
    String? split,
    bool? hasWarnings,
  }) async {
    final items = await _client.datasetVersionSamples(
      datasetVersionId,
      split: split,
      hasWarnings: hasWarnings,
    );
    return items
        .whereType<Map>()
        .map(DatasetVersionSampleDto.fromMap)
        .toList(growable: false);
  }

  Future<TrainingRecipeDto> recommendRecipe({
    required String datasetVersionId,
    required RecipeRecommendRequestDto request,
  }) async {
    final body = await _client.recommendDatasetRecipe(
      datasetVersionId,
      request.toMap(),
    );
    return TrainingRecipeDto.fromMap(body);
  }

  Future<List<TrainingRecipeDto>> listRecipes(String datasetVersionId) async {
    final items = await _client.datasetVersionRecipes(datasetVersionId);
    return items
        .whereType<Map>()
        .map(TrainingRecipeDto.fromMap)
        .toList(growable: false);
  }

  Future<TrainingRecipeDto> updateRecipe(
    String recipeId,
    Map<String, Object?> body,
  ) async {
    final response = await _client.updateDatasetRecipe(recipeId, body);
    return TrainingRecipeDto.fromMap(response);
  }

  Future<TrainingRecipeDto> confirmRecipe(String recipeId) async {
    final body = await _client.confirmDatasetRecipe(recipeId);
    return TrainingRecipeDto.fromMap(body);
  }
}
