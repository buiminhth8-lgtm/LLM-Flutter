import '../../core/api/api_client.dart';
import '../revisions/models/revision_record_dto.dart';
import 'models/adapter_eval_case_dto.dart';
import 'models/adapter_eval_create_request_dto.dart';
import 'models/adapter_eval_report_dto.dart';
import 'models/adapter_eval_score_dto.dart';
import 'models/adapter_eval_session_dto.dart';

class AdapterEvalApiClient {
  AdapterEvalApiClient(this._client);

  final LlmStudioClient _client;

  Future<AdapterEvalSessionDto> createSession(
    CreateAdapterEvalSessionRequest request,
  ) async {
    final body = await _client.createAdapterEvalSession(request.toMap());
    return AdapterEvalSessionDto.fromMap(body);
  }

  Future<List<AdapterEvalSessionDto>> listSessions({
    String? status,
    String? projectId,
    String? adapterId,
  }) async {
    final items = await _client.adapterEvalSessions(
      status: status,
      projectId: projectId,
      adapterId: adapterId,
    );
    return items
        .whereType<Map>()
        .map(AdapterEvalSessionDto.fromMap)
        .toList(growable: false);
  }

  Future<AdapterEvalSessionDto> getSession(String sessionId) async {
    final body = await _client.adapterEvalSession(sessionId);
    return AdapterEvalSessionDto.fromMap(body);
  }

  Future<AdapterEvalCaseDto> createCase(
    String sessionId,
    CreateAdapterEvalCaseRequest request,
  ) async {
    final body = await _client.createAdapterEvalCase(
      sessionId,
      request.toMap(),
    );
    return AdapterEvalCaseDto.fromMap(body);
  }

  Future<AdapterEvalCaseDto> getCase(String caseId) async {
    final body = await _client.adapterEvalCase(caseId);
    return AdapterEvalCaseDto.fromMap(body);
  }

  Future<AdapterEvalCaseDto> prepareCase(String caseId) async {
    final body = await _client.prepareAdapterEvalCase(caseId);
    return AdapterEvalCaseDto.fromMap(body);
  }

  Future<AdapterEvalCaseDto> runCase(String caseId) async {
    final body = await _client.runAdapterEvalCase(caseId);
    return AdapterEvalCaseDto.fromMap(body);
  }

  Future<AdapterEvalSessionDto> runSession(String sessionId) async {
    final body = await _client.runAdapterEvalSession(sessionId);
    return AdapterEvalSessionDto.fromMap(body);
  }

  Future<AdapterEvalScoreDto> scoreCase(
    String caseId,
    AdapterEvalScoreRequest request,
  ) async {
    final body = await _client.scoreAdapterEvalCase(caseId, request.toMap());
    return AdapterEvalScoreDto.fromMap(body);
  }

  Future<AdapterEvalReportDto> generateReport(String sessionId) async {
    final body = await _client.generateAdapterEvalReport(sessionId);
    return AdapterEvalReportDto.fromMap(body);
  }

  Future<List<AdapterEvalReportDto>> listReports(String sessionId) async {
    final items = await _client.adapterEvalReports(sessionId);
    return items
        .whereType<Map>()
        .map(AdapterEvalReportDto.fromMap)
        .toList(growable: false);
  }

  Future<RevisionRecordDto> createRevisionFromEvalResult(
    String resultId,
    CreateRevisionFromEvalResultRequest request,
  ) async {
    final body = await _client.createRevisionFromEvalResult(
      resultId,
      request.toMap(),
    );
    return RevisionRecordDto.fromMap(body);
  }
}
