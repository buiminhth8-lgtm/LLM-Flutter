import 'dart:async';

import 'package:flutter/foundation.dart';

import '../../core/api/api_exception.dart';
import 'models/revision_autosave_dto.dart';
import 'models/revision_record_dto.dart';
import 'revision_api_client.dart';
import 'revision_state.dart';

class RevisionController extends ChangeNotifier {
  RevisionController(this._api);

  final RevisionApiClient _api;
  Timer? _autosaveTimer;
  int _clientRevision = 0;
  RevisionState state = const RevisionState();

  Future<void> refresh() async {
    await _run(() async {
      final revisions = await _api.listRevisions(
        projectId: state.selectedProjectId,
        chapterId: state.selectedChapterId,
        status: state.selectedStatus,
        userScore: state.selectedScore,
      );
      state = state.copyWith(revisions: revisions);
    });
  }

  Future<void> setFilters({
    String? projectId,
    String? chapterId,
    String? status,
    int? score,
    bool clearProject = false,
    bool clearChapter = false,
    bool clearStatus = false,
    bool clearScore = false,
  }) async {
    state = state.copyWith(
      selectedProjectId: projectId,
      selectedChapterId: chapterId,
      selectedStatus: status,
      selectedScore: score,
      clearProject: clearProject,
      clearChapter: clearChapter,
      clearStatus: clearStatus,
      clearScore: clearScore,
    );
    notifyListeners();
    await refresh();
  }

  Future<void> openRevision(String revisionId) async {
    await _run(() async {
      final revision = await _api.getRevision(revisionId);
      _clientRevision = 0;
      state = _stateForCurrent(revision);
    });
  }

  Future<RevisionRecordDto?> createFromGeneration(
    String generationId, {
    String? editedText,
  }) async {
    RevisionRecordDto? created;
    await _run(() async {
      created = await _api.createRevisionFromGeneration(
        generationId: generationId,
        editedText: editedText,
      );
      _clientRevision = 0;
      state = _stateForCurrent(
        created!,
        revisions: await _api.listRevisions(
          projectId: created!.projectId,
          chapterId: created!.chapterId,
        ),
      );
    });
    return created;
  }

  Future<void> saveCurrent(String editedText) async {
    final current = state.current;
    if (current == null) {
      _setError('请先选择一个修订记录。');
      return;
    }
    state = state.copyWith(saving: true, clearError: true, clearNotice: true);
    notifyListeners();
    try {
      final revision = await _api.updateRevision(
        current.revisionId,
        RevisionUpdateRequest(
          editedText: editedText,
          editTags: state.editTags,
          userScore: state.userScore,
          qualityNotes: state.qualityNotes,
          acceptedForDataset: state.acceptedForDataset,
          expectedUpdatedAt: current.updatedAt,
        ),
      );
      _clientRevision = 0;
      state = _stateForCurrent(
        revision,
        revisions: await _api.listRevisions(
          projectId: revision.projectId,
          chapterId: revision.chapterId,
        ),
      ).copyWith(saving: false, notice: 'Revision saved.');
    } catch (error) {
      state = state.copyWith(saving: false, error: _message(error));
    }
    notifyListeners();
  }

  void setTags(List<String> tags) {
    state = state.copyWith(editTags: tags);
    notifyListeners();
  }

  void setScore(int? score) {
    state = state.copyWith(userScore: score, clearUserScore: score == null);
    notifyListeners();
  }

  void setQualityNotes(String notes) {
    state = state.copyWith(qualityNotes: notes);
    notifyListeners();
  }

  Future<void> setDatasetCandidate(bool accepted) async {
    final current = state.current;
    if (current == null) {
      state = state.copyWith(acceptedForDataset: accepted);
      notifyListeners();
      return;
    }
    await _run(() async {
      final revision = await _api.markDatasetCandidate(
        current.revisionId,
        accepted,
      );
      state = _stateForCurrent(revision);
    });
  }

  Future<void> approveCurrent() async {
    final current = state.current;
    if (current == null) {
      return;
    }
    await _run(() async {
      state = _stateForCurrent(await _api.approveRevision(current.revisionId));
    });
  }

  Future<void> rejectCurrent({String? reason}) async {
    final current = state.current;
    if (current == null) {
      return;
    }
    await _run(() async {
      state = _stateForCurrent(
        await _api.rejectRevision(current.revisionId, reason: reason),
      );
    });
  }

  Future<void> archiveCurrent() async {
    final current = state.current;
    if (current == null) {
      return;
    }
    await _run(() async {
      final revision = await _api.updateRevision(
        current.revisionId,
        const RevisionUpdateRequest(status: 'archived'),
      );
      state = _stateForCurrent(revision);
    });
  }

  void scheduleAutosave(String text) {
    _autosaveTimer?.cancel();
    _autosaveTimer = Timer(
      const Duration(seconds: 4),
      () => unawaited(autosave(text)),
    );
  }

  Future<void> flushAutosave(String text) async {
    _autosaveTimer?.cancel();
    await autosave(text);
  }

  Future<void> autosave(String text) async {
    final current = state.current;
    if (current == null || text.trim().isEmpty) {
      return;
    }
    _clientRevision += 1;
    state = state.copyWith(autosaving: true);
    notifyListeners();
    try {
      final autosave = await _api.autosaveRevision(
        RevisionAutosaveRequest(
          revisionId: current.revisionId,
          projectId: current.projectId,
          chapterId: current.chapterId,
          generationId: current.generationId,
          draftText: text,
          baseTextHash: current.editedHash,
          clientRevision: _clientRevision,
        ),
      );
      state = state.copyWith(
        autosaving: false,
        lastAutosaveAt: autosave.createdAt,
        clearError: true,
      );
    } catch (error) {
      state = state.copyWith(autosaving: false, error: _message(error));
    }
    notifyListeners();
  }

  RevisionState _stateForCurrent(
    RevisionRecordDto revision, {
    List<RevisionRecordDto>? revisions,
  }) => state.copyWith(
    revisions: revisions,
    current: revision,
    editTags: revision.editTags,
    userScore: revision.userScore,
    clearUserScore: revision.userScore == null,
    qualityNotes: revision.qualityNotes ?? '',
    acceptedForDataset: revision.acceptedForDataset,
    notice: revision.warnings.isEmpty
        ? null
        : revision.warnings.map((item) => item['message']).join('\n'),
    clearNotice: revision.warnings.isEmpty,
    clearError: true,
  );

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

  void _setError(String message) {
    state = state.copyWith(error: message);
    notifyListeners();
  }

  static String _message(Object error) =>
      error is StudioApiException ? error.toString() : '$error';

  @override
  void dispose() {
    _autosaveTimer?.cancel();
    super.dispose();
  }
}
