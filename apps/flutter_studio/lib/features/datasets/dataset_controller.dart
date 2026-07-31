import 'package:flutter/foundation.dart';

import '../../core/api/api_exception.dart';
import 'dataset_api_client.dart';
import 'dataset_state.dart';
import 'models/dataset_export_dto.dart';
import 'models/dataset_freeze_request_dto.dart';
import 'models/dataset_version_dto.dart';
import 'models/recipe_recommend_request_dto.dart';
import 'models/training_dataset_dto.dart';
import 'models/training_recipe_dto.dart';
import 'models/training_sample_dto.dart';

class DatasetController extends ChangeNotifier {
  DatasetController(this._api);

  final DatasetApiClient _api;
  DatasetState state = const DatasetState();

  Future<void> refresh() async {
    await _run(() async {
      final datasets = await _api.listDatasets(
        projectId: state.selectedProjectId,
        type: state.selectedType,
        status: state.selectedStatus,
      );
      state = state.copyWith(datasets: datasets);
      final current = state.currentDataset;
      if (current != null &&
          datasets.any((item) => item.datasetId == current.datasetId)) {
        await _loadDataset(current.datasetId);
      }
    });
  }

  Future<void> setFilters({
    String? projectId,
    String? type,
    String? status,
    bool clearProject = false,
    bool clearType = false,
    bool clearStatus = false,
  }) async {
    state = state.copyWith(
      selectedProjectId: projectId,
      selectedType: type,
      selectedStatus: status,
      clearProject: clearProject,
      clearType: clearType,
      clearStatus: clearStatus,
    );
    notifyListeners();
    await refresh();
  }

  Future<void> createDataset(CreateDatasetRequest request) async {
    await _run(() async {
      final dataset = await _api.createDataset(request);
      state = state.copyWith(
        currentDataset: dataset,
        currentSample: null,
        currentVersion: null,
        currentManifest: null,
        currentRecipe: null,
        datasets: await _api.listDatasets(projectId: dataset.projectId),
        samples: const [],
        exports: const [],
        versions: const [],
        versionSamples: const [],
        recipes: const [],
        notice: 'Dataset created.',
      );
      await _loadDataset(dataset.datasetId);
    });
  }

  Future<void> selectDataset(String datasetId) async {
    await _run(() async {
      await _loadDataset(datasetId);
    });
  }

  Future<TrainingSampleDto?> createSampleFromRevision({
    required String datasetId,
    required String revisionId,
    String sampleType = 'sft',
  }) async {
    TrainingSampleDto? sample;
    await _run(() async {
      sample = await _api.createSampleFromRevision(
        datasetId: datasetId,
        revisionId: revisionId,
        sampleType: sampleType,
      );
      await _loadDataset(datasetId, selectedSample: sample);
      state = state.copyWith(notice: 'Sample created from revision.');
    });
    return sample;
  }

  Future<void> bulkCreateSamples({
    required String datasetId,
    String? projectId,
    String? chapterId,
    int? minScore,
    List<String>? tags,
  }) async {
    await _run(() async {
      final result = await _api.bulkCreateSamplesFromRevisions(
        datasetId: datasetId,
        projectId: projectId,
        chapterId: chapterId,
        minScore: minScore,
        tags: tags,
      );
      await _loadDataset(datasetId);
      state = state.copyWith(
        notice:
            'Bulk created ${result.createdCount} samples, ${result.errorCount} errors.',
      );
    });
  }

  void selectSample(TrainingSampleDto sample) {
    state = state.copyWith(currentSample: sample);
    notifyListeners();
  }

  Future<void> updateCurrentSample(UpdateSampleRequest request) async {
    final sample = state.currentSample;
    if (sample == null) {
      return;
    }
    await _run(() async {
      final updated = await _api.updateSample(sample.sampleId, request);
      await _loadDataset(updated.datasetId, selectedSample: updated);
      state = state.copyWith(notice: 'Sample saved.');
    });
  }

  Future<void> approveCurrentSample() async {
    final sample = state.currentSample;
    if (sample == null) {
      return;
    }
    await _run(() async {
      final updated = await _api.approveSample(sample.sampleId);
      await _loadDataset(updated.datasetId, selectedSample: updated);
    });
  }

  Future<void> rejectCurrentSample({String? reason}) async {
    final sample = state.currentSample;
    if (sample == null) {
      return;
    }
    await _run(() async {
      final updated = await _api.rejectSample(sample.sampleId, reason: reason);
      await _loadDataset(updated.datasetId, selectedSample: updated);
    });
  }

  Future<DatasetExportDto?> exportCurrentDataset({
    String format = 'sft_jsonl',
    bool approvedOnly = true,
  }) async {
    final dataset = state.currentDataset;
    if (dataset == null) {
      return null;
    }
    DatasetExportDto? export;
    await _run(() async {
      export = await _api.exportDataset(
        datasetId: dataset.datasetId,
        format: format,
        approvedOnly: approvedOnly,
      );
      await _loadDataset(dataset.datasetId);
      state = state.copyWith(notice: 'Dataset exported: ${export!.exportPath}');
    });
    return export;
  }

  Future<void> markCurrentDatasetReady() async {
    final dataset = state.currentDataset;
    if (dataset == null) {
      return;
    }
    await _run(() async {
      await _api.markReady(dataset.datasetId);
      await _loadDataset(dataset.datasetId);
      state = state.copyWith(notice: 'Dataset marked ready for freeze.');
    });
  }

  Future<DatasetVersionDto?> freezeCurrentDataset(
    DatasetFreezeRequestDto request,
  ) async {
    final dataset = state.currentDataset;
    if (dataset == null) {
      return null;
    }
    DatasetVersionDto? version;
    await _run(() async {
      version = await _api.freezeDataset(
        datasetId: dataset.datasetId,
        request: request,
      );
      await _loadDataset(dataset.datasetId, selectedVersion: version);
      await selectVersion(version!.datasetVersionId);
      state = state.copyWith(notice: 'Dataset frozen as v${version!.version}.');
    });
    return version;
  }

  Future<void> selectVersion(String datasetVersionId) async {
    await _run(() async {
      final version = await _api.getVersion(datasetVersionId);
      final samples = await _api.listVersionSamples(datasetVersionId);
      final manifest = await _api.getManifest(datasetVersionId);
      final recipes = await _api.listRecipes(datasetVersionId);
      state = state.copyWith(
        currentVersion: version,
        versionSamples: samples,
        currentManifest: manifest,
        recipes: recipes,
        currentRecipe: recipes.isEmpty ? null : recipes.first,
        clearRecipe: recipes.isEmpty,
      );
    });
  }

  Future<TrainingRecipeDto?> recommendRecipe(
    RecipeRecommendRequestDto request,
  ) async {
    final version = state.currentVersion;
    if (version == null) {
      return null;
    }
    TrainingRecipeDto? recipe;
    await _run(() async {
      recipe = await _api.recommendRecipe(
        datasetVersionId: version.datasetVersionId,
        request: request,
      );
      final recipes = await _api.listRecipes(version.datasetVersionId);
      state = state.copyWith(
        recipes: recipes,
        currentRecipe: recipe,
        notice: 'Recipe recommendation created.',
      );
    });
    return recipe;
  }

  Future<void> updateCurrentRecipe(Map<String, Object?> body) async {
    final recipe = state.currentRecipe;
    if (recipe == null) {
      return;
    }
    await _run(() async {
      final updated = await _api.updateRecipe(recipe.recipeId, body);
      state = state.copyWith(currentRecipe: updated);
    });
  }

  Future<void> confirmCurrentRecipe() async {
    final recipe = state.currentRecipe;
    if (recipe == null) {
      return;
    }
    await _run(() async {
      final confirmed = await _api.confirmRecipe(recipe.recipeId);
      state = state.copyWith(
        currentRecipe: confirmed,
        notice: 'Recipe confirmed. Training is still Stage 8.',
      );
    });
  }

  Future<void> _loadDataset(
    String datasetId, {
    TrainingSampleDto? selectedSample,
    DatasetVersionDto? selectedVersion,
  }) async {
    final dataset = await _api.getDataset(datasetId);
    final samples = await _api.listSamples(datasetId: datasetId);
    final exports = await _api.listExports(datasetId);
    final versions = await _api.listVersions(datasetId);
    final sample = selectedSample ?? _selectedSample(samples);
    final version = selectedVersion ?? _selectedVersion(versions);
    state = state.copyWith(
      currentDataset: dataset,
      samples: samples,
      exports: exports,
      versions: versions,
      currentVersion: version,
      currentSample: sample,
      clearSample: sample == null,
      clearVersion: version == null,
      clearManifest: version == null,
      clearRecipe: version == null,
    );
  }

  Future<void> _run(Future<void> Function() action) async {
    state = state.copyWith(loading: true, clearError: true, clearNotice: true);
    notifyListeners();
    try {
      await action();
      state = state.copyWith(loading: false);
    } catch (error) {
      state = state.copyWith(loading: false, error: _message(error));
    }
    notifyListeners();
  }

  static String _message(Object error) =>
      error is StudioApiException ? error.toString() : '$error';

  TrainingSampleDto? _selectedSample(List<TrainingSampleDto> samples) {
    final current = state.currentSample;
    if (current == null) {
      return samples.isEmpty ? null : samples.first;
    }
    for (final sample in samples) {
      if (sample.sampleId == current.sampleId) {
        return sample;
      }
    }
    return samples.isEmpty ? null : samples.first;
  }

  DatasetVersionDto? _selectedVersion(List<DatasetVersionDto> versions) {
    final current = state.currentVersion;
    if (current == null) {
      return versions.isEmpty ? null : versions.first;
    }
    for (final version in versions) {
      if (version.datasetVersionId == current.datasetVersionId) {
        return version;
      }
    }
    return versions.isEmpty ? null : versions.first;
  }
}
