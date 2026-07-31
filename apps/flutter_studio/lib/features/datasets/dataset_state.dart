import 'models/dataset_export_dto.dart';
import 'models/dataset_manifest_dto.dart';
import 'models/dataset_version_dto.dart';
import 'models/dataset_version_sample_dto.dart';
import 'models/training_dataset_dto.dart';
import 'models/training_recipe_dto.dart';
import 'models/training_sample_dto.dart';

class DatasetState {
  const DatasetState({
    this.datasets = const [],
    this.samples = const [],
    this.exports = const [],
    this.versions = const [],
    this.versionSamples = const [],
    this.recipes = const [],
    this.currentDataset,
    this.currentSample,
    this.currentVersion,
    this.currentManifest,
    this.currentRecipe,
    this.selectedProjectId,
    this.selectedType,
    this.selectedStatus,
    this.loading = false,
    this.saving = false,
    this.error,
    this.notice,
  });

  final List<TrainingDatasetDto> datasets;
  final List<TrainingSampleDto> samples;
  final List<DatasetExportDto> exports;
  final List<DatasetVersionDto> versions;
  final List<DatasetVersionSampleDto> versionSamples;
  final List<TrainingRecipeDto> recipes;
  final TrainingDatasetDto? currentDataset;
  final TrainingSampleDto? currentSample;
  final DatasetVersionDto? currentVersion;
  final DatasetManifestDto? currentManifest;
  final TrainingRecipeDto? currentRecipe;
  final String? selectedProjectId;
  final String? selectedType;
  final String? selectedStatus;
  final bool loading;
  final bool saving;
  final String? error;
  final String? notice;

  DatasetState copyWith({
    List<TrainingDatasetDto>? datasets,
    List<TrainingSampleDto>? samples,
    List<DatasetExportDto>? exports,
    List<DatasetVersionDto>? versions,
    List<DatasetVersionSampleDto>? versionSamples,
    List<TrainingRecipeDto>? recipes,
    TrainingDatasetDto? currentDataset,
    TrainingSampleDto? currentSample,
    DatasetVersionDto? currentVersion,
    DatasetManifestDto? currentManifest,
    TrainingRecipeDto? currentRecipe,
    String? selectedProjectId,
    String? selectedType,
    String? selectedStatus,
    bool? loading,
    bool? saving,
    String? error,
    String? notice,
    bool clearDataset = false,
    bool clearSample = false,
    bool clearVersion = false,
    bool clearManifest = false,
    bool clearRecipe = false,
    bool clearProject = false,
    bool clearType = false,
    bool clearStatus = false,
    bool clearError = false,
    bool clearNotice = false,
  }) => DatasetState(
    datasets: datasets ?? this.datasets,
    samples: samples ?? this.samples,
    exports: exports ?? this.exports,
    versions: versions ?? this.versions,
    versionSamples: versionSamples ?? this.versionSamples,
    recipes: recipes ?? this.recipes,
    currentDataset: clearDataset ? null : currentDataset ?? this.currentDataset,
    currentSample: clearSample ? null : currentSample ?? this.currentSample,
    currentVersion: clearVersion ? null : currentVersion ?? this.currentVersion,
    currentManifest: clearManifest
        ? null
        : currentManifest ?? this.currentManifest,
    currentRecipe: clearRecipe ? null : currentRecipe ?? this.currentRecipe,
    selectedProjectId: clearProject
        ? null
        : selectedProjectId ?? this.selectedProjectId,
    selectedType: clearType ? null : selectedType ?? this.selectedType,
    selectedStatus: clearStatus ? null : selectedStatus ?? this.selectedStatus,
    loading: loading ?? this.loading,
    saving: saving ?? this.saving,
    error: clearError ? null : error ?? this.error,
    notice: clearNotice ? null : notice ?? this.notice,
  );
}
