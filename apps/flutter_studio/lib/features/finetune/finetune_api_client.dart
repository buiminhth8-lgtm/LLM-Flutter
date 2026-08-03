import '../../core/api/api_client.dart';
import 'models/finetune_checkpoint_dto.dart';
import 'models/finetune_create_run_request_dto.dart';
import 'models/finetune_log_dto.dart';
import 'models/finetune_metric_dto.dart';
import 'models/finetune_preflight_dto.dart';
import 'models/finetune_run_dto.dart';

class FinetuneApiClient {
  FinetuneApiClient(this._client);

  final LlmStudioClient _client;

  Future<FinetunePreflightDto> preflightFinetune(
    FinetunePreflightRequestDto request,
  ) async {
    final body = await _client.preflightFinetune(request.toMap());
    return FinetunePreflightDto.fromMap(body);
  }

  Future<FinetuneRunDto> createFinetuneRun(
    FinetuneCreateRunRequestDto request,
  ) async {
    final body = await _client.createFinetuneRun(request.toMap());
    return FinetuneRunDto.fromMap(body);
  }

  Future<List<FinetuneRunDto>> listFinetuneRuns({
    String? status,
    String? datasetVersionId,
    String? baseModelId,
    String? method,
  }) async {
    final items = await _client.finetuneRuns(
      status: status,
      datasetVersionId: datasetVersionId,
      baseModelId: baseModelId,
      method: method,
    );
    return items
        .whereType<Map>()
        .map(FinetuneRunDto.fromMap)
        .toList(growable: false);
  }

  Future<FinetuneRunDto> getFinetuneRun(String runId) async {
    final body = await _client.finetuneRun(runId);
    return FinetuneRunDto.fromMap(body);
  }

  Future<FinetuneRunDto> startFinetuneRun(String runId) async {
    final body = await _client.startFinetuneRun(runId);
    return FinetuneRunDto.fromMap(body);
  }

  Future<FinetuneRunDto> cancelFinetuneRun(String runId) async {
    final body = await _client.cancelFinetuneRun(runId);
    return FinetuneRunDto.fromMap(body);
  }

  Future<FinetuneRunDto> resumeFinetuneRun(
    String runId, {
    String? checkpointId,
  }) async {
    final body = await _client.resumeFinetuneRun(
      runId,
      checkpointId: checkpointId,
    );
    return FinetuneRunDto.fromMap(body);
  }

  Future<List<FinetuneMetricDto>> getFinetuneMetrics(String runId) async {
    final items = await _client.finetuneMetrics(runId);
    return items
        .whereType<Map>()
        .map(FinetuneMetricDto.fromMap)
        .toList(growable: false);
  }

  Future<List<FinetuneLogDto>> getFinetuneLogs(String runId) async {
    final items = await _client.finetuneLogs(runId);
    return items
        .whereType<Map>()
        .map(FinetuneLogDto.fromMap)
        .toList(growable: false);
  }

  Future<List<FinetuneCheckpointDto>> getFinetuneCheckpoints(
    String runId,
  ) async {
    final items = await _client.finetuneCheckpoints(runId);
    return items
        .whereType<Map>()
        .map(FinetuneCheckpointDto.fromMap)
        .toList(growable: false);
  }
}
