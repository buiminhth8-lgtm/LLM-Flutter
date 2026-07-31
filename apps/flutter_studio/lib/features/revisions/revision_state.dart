import 'models/revision_record_dto.dart';

class RevisionState {
  const RevisionState({
    this.revisions = const [],
    this.current,
    this.selectedProjectId,
    this.selectedChapterId,
    this.selectedStatus,
    this.selectedScore,
    this.editTags = const [],
    this.userScore,
    this.qualityNotes = '',
    this.acceptedForDataset = false,
    this.loading = false,
    this.saving = false,
    this.autosaving = false,
    this.error,
    this.notice,
    this.lastAutosaveAt,
  });

  final List<RevisionRecordDto> revisions;
  final RevisionRecordDto? current;
  final String? selectedProjectId;
  final String? selectedChapterId;
  final String? selectedStatus;
  final int? selectedScore;
  final List<String> editTags;
  final int? userScore;
  final String qualityNotes;
  final bool acceptedForDataset;
  final bool loading;
  final bool saving;
  final bool autosaving;
  final String? error;
  final String? notice;
  final String? lastAutosaveAt;

  RevisionState copyWith({
    List<RevisionRecordDto>? revisions,
    RevisionRecordDto? current,
    String? selectedProjectId,
    String? selectedChapterId,
    String? selectedStatus,
    int? selectedScore,
    List<String>? editTags,
    int? userScore,
    String? qualityNotes,
    bool? acceptedForDataset,
    bool? loading,
    bool? saving,
    bool? autosaving,
    String? error,
    String? notice,
    String? lastAutosaveAt,
    bool clearCurrent = false,
    bool clearProject = false,
    bool clearChapter = false,
    bool clearStatus = false,
    bool clearScore = false,
    bool clearUserScore = false,
    bool clearError = false,
    bool clearNotice = false,
    bool clearAutosave = false,
  }) => RevisionState(
    revisions: revisions ?? this.revisions,
    current: clearCurrent ? null : current ?? this.current,
    selectedProjectId: clearProject
        ? null
        : selectedProjectId ?? this.selectedProjectId,
    selectedChapterId: clearChapter
        ? null
        : selectedChapterId ?? this.selectedChapterId,
    selectedStatus: clearStatus ? null : selectedStatus ?? this.selectedStatus,
    selectedScore: clearScore ? null : selectedScore ?? this.selectedScore,
    editTags: editTags ?? this.editTags,
    userScore: clearUserScore ? null : userScore ?? this.userScore,
    qualityNotes: qualityNotes ?? this.qualityNotes,
    acceptedForDataset: acceptedForDataset ?? this.acceptedForDataset,
    loading: loading ?? this.loading,
    saving: saving ?? this.saving,
    autosaving: autosaving ?? this.autosaving,
    error: clearError ? null : error ?? this.error,
    notice: clearNotice ? null : notice ?? this.notice,
    lastAutosaveAt: clearAutosave
        ? null
        : lastAutosaveAt ?? this.lastAutosaveAt,
  );
}
