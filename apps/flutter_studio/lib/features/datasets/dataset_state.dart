import 'models/dataset_export_dto.dart';
import 'models/training_dataset_dto.dart';
import 'models/training_sample_dto.dart';

class DatasetState {
  const DatasetState({
    this.datasets = const [],
    this.samples = const [],
    this.exports = const [],
    this.currentDataset,
    this.currentSample,
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
  final TrainingDatasetDto? currentDataset;
  final TrainingSampleDto? currentSample;
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
    TrainingDatasetDto? currentDataset,
    TrainingSampleDto? currentSample,
    String? selectedProjectId,
    String? selectedType,
    String? selectedStatus,
    bool? loading,
    bool? saving,
    String? error,
    String? notice,
    bool clearDataset = false,
    bool clearSample = false,
    bool clearProject = false,
    bool clearType = false,
    bool clearStatus = false,
    bool clearError = false,
    bool clearNotice = false,
  }) => DatasetState(
    datasets: datasets ?? this.datasets,
    samples: samples ?? this.samples,
    exports: exports ?? this.exports,
    currentDataset: clearDataset ? null : currentDataset ?? this.currentDataset,
    currentSample: clearSample ? null : currentSample ?? this.currentSample,
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
