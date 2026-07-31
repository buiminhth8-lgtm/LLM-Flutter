import '../../core/api/api_client.dart';
import 'models/revision_autosave_dto.dart';
import 'models/revision_record_dto.dart';

class RevisionApiClient {
  RevisionApiClient(this._client);

  final LlmStudioClient _client;

  Future<RevisionRecordDto> createRevisionFromGeneration({
    required String generationId,
    String? editedText,
    List<String> editTags = const [],
    int? userScore,
    String? qualityNotes,
    bool acceptedForDataset = false,
  }) async {
    final request = <String, Object?>{
      'generation_id': generationId,
      'edit_tags': editTags,
      'accepted_for_dataset': acceptedForDataset,
    };
    if (editedText != null) {
      request['edited_text'] = editedText;
    }
    if (userScore != null) {
      request['user_score'] = userScore;
    }
    if (qualityNotes != null) {
      request['quality_notes'] = qualityNotes;
    }
    final body = await _client.createRevisionFromGeneration(request);
    return RevisionRecordDto.fromMap(body);
  }

  Future<RevisionRecordDto> createRevisionFromChapterDraft({
    required String projectId,
    required String chapterId,
    String? sceneId,
    String? originalText,
    required String editedText,
    List<String> editTags = const [],
    int? userScore,
    String? qualityNotes,
    bool acceptedForDataset = false,
  }) async {
    final request = <String, Object?>{
      'project_id': projectId,
      'chapter_id': chapterId,
      'edited_text': editedText,
      'edit_tags': editTags,
      'accepted_for_dataset': acceptedForDataset,
    };
    if (sceneId != null) {
      request['scene_id'] = sceneId;
    }
    if (originalText != null) {
      request['original_text'] = originalText;
    }
    if (userScore != null) {
      request['user_score'] = userScore;
    }
    if (qualityNotes != null) {
      request['quality_notes'] = qualityNotes;
    }
    final body = await _client.createRevisionFromChapterDraft(request);
    return RevisionRecordDto.fromMap(body);
  }

  Future<RevisionRecordDto> createManualRevision({
    required String projectId,
    String? chapterId,
    String? sceneId,
    required String originalText,
    required String editedText,
    List<String> editTags = const [],
    int? userScore,
    String? qualityNotes,
    bool acceptedForDataset = false,
  }) async {
    final request = <String, Object?>{
      'project_id': projectId,
      'original_text': originalText,
      'edited_text': editedText,
      'edit_tags': editTags,
      'accepted_for_dataset': acceptedForDataset,
    };
    if (chapterId != null) {
      request['chapter_id'] = chapterId;
    }
    if (sceneId != null) {
      request['scene_id'] = sceneId;
    }
    if (userScore != null) {
      request['user_score'] = userScore;
    }
    if (qualityNotes != null) {
      request['quality_notes'] = qualityNotes;
    }
    final body = await _client.createManualRevision(request);
    return RevisionRecordDto.fromMap(body);
  }

  Future<RevisionRecordDto> updateRevision(
    String revisionId,
    RevisionUpdateRequest request,
  ) async {
    final body = await _client.updateRevision(revisionId, request.toMap());
    return RevisionRecordDto.fromMap(body);
  }

  Future<RevisionRecordDto> getRevision(String revisionId) async {
    final body = await _client.revision(revisionId);
    return RevisionRecordDto.fromMap(body);
  }

  Future<List<RevisionRecordDto>> listRevisions({
    String? projectId,
    String? chapterId,
    String? generationId,
    String? status,
    int? userScore,
  }) async {
    final items = await _client.revisions(
      projectId: projectId,
      chapterId: chapterId,
      generationId: generationId,
      status: status,
      userScore: userScore,
    );
    return items
        .whereType<Map>()
        .map(RevisionRecordDto.fromMap)
        .toList(growable: false);
  }

  Future<RevisionRecordDto> approveRevision(String revisionId) async {
    final body = await _client.approveRevision(revisionId);
    return RevisionRecordDto.fromMap(body);
  }

  Future<RevisionRecordDto> rejectRevision(
    String revisionId, {
    String? reason,
  }) async {
    final body = await _client.rejectRevision(revisionId, reason: reason);
    return RevisionRecordDto.fromMap(body);
  }

  Future<RevisionRecordDto> markDatasetCandidate(
    String revisionId,
    bool accepted,
  ) async {
    final body = await _client.markRevisionDatasetCandidate(
      revisionId,
      accepted,
    );
    return RevisionRecordDto.fromMap(body);
  }

  Future<RevisionAutosaveDto> autosaveRevision(
    RevisionAutosaveRequest request,
  ) async {
    final body = await _client.autosaveRevision(request.toMap());
    return RevisionAutosaveDto.fromMap(body);
  }

  Future<List<RevisionAutosaveDto>> listAutosaves(String revisionId) async {
    final items = await _client.revisionAutosaves(revisionId);
    return items
        .whereType<Map>()
        .map(RevisionAutosaveDto.fromMap)
        .toList(growable: false);
  }
}
