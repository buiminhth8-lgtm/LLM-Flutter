import '../../core/api/api_client.dart';
import 'models/evaluation_finding_dto.dart';
import 'models/evaluation_metric_dto.dart';
import 'models/evaluation_report_dto.dart';
import 'models/evaluation_run_dto.dart';
import 'models/manual_evaluation_score_dto.dart';

const evaluationTargetTypeLabels = <String, String>{
  'project': '项目',
  'chapter': '章节',
  'generation': '写作生成',
  'revision': '修订',
  'memory_retrieval': '记忆检索',
  'adapter_eval_session': '适配器评估会话',
};

const evaluationEvaluatorLabels = <String, String>{
  'repetition': '重复度',
  'style_consistency': '文风一致性',
  'character_consistency': '人物一致性',
  'world_consistency': '世界观一致性',
  'plot_coherence': '剧情连贯性',
  'pacing': '节奏',
  'memory_usage': '记忆使用',
  'foreshadowing': '伏笔',
  'local_model_judge': '本地模型裁判',
};

const defaultEvaluationEvaluators = <String>[
  'repetition',
  'style_consistency',
  'character_consistency',
  'world_consistency',
  'plot_coherence',
  'pacing',
  'memory_usage',
  'foreshadowing',
];

class EvaluationApiClient {
  EvaluationApiClient(this._client);

  final LlmStudioClient _client;

  Future<List<EvaluationRunDto>> listRuns({
    String? projectId,
    String? targetType,
    String? status,
  }) async {
    final items = await _client.evaluationRuns(
      projectId: projectId,
      targetType: targetType,
      status: status,
    );
    return items
        .whereType<Map>()
        .map(EvaluationRunDto.fromMap)
        .toList(growable: false);
  }

  Future<EvaluationRunDto> createRun(CreateEvaluationRunRequest request) async {
    final body = await _client.createEvaluationRun(request.toMap());
    return EvaluationRunDto.fromMap(body);
  }

  Future<EvaluationRunDto> runSync(CreateEvaluationRunRequest request) async {
    final body = await _client.runEvaluationSync(request.toMap());
    return EvaluationRunDto.fromMap(body);
  }

  Future<EvaluationRunDto> getRun(String runId) async {
    final body = await _client.evaluationRun(runId);
    return EvaluationRunDto.fromMap(body);
  }

  Future<EvaluationRunDto> startRun(String runId) async {
    final body = await _client.startEvaluationRun(runId);
    return EvaluationRunDto.fromMap(body);
  }

  Future<EvaluationRunDto> cancelRun(String runId) async {
    final body = await _client.cancelEvaluationRun(runId);
    return EvaluationRunDto.fromMap(body);
  }

  Future<EvaluationRunDto> archiveRun(String runId) async {
    final body = await _client.archiveEvaluationRun(runId);
    return EvaluationRunDto.fromMap(body);
  }

  Future<List<EvaluationMetricDto>> listMetrics(String runId) async {
    final items = await _client.evaluationMetrics(runId);
    return items
        .whereType<Map>()
        .map(EvaluationMetricDto.fromMap)
        .toList(growable: false);
  }

  Future<List<EvaluationFindingDto>> listFindings(
    String runId, {
    String? category,
    String? severity,
    String? status,
  }) async {
    final items = await _client.evaluationFindings(
      runId,
      category: category,
      severity: severity,
      status: status,
    );
    return items
        .whereType<Map>()
        .map(EvaluationFindingDto.fromMap)
        .toList(growable: false);
  }

  Future<EvaluationFindingDto> updateFindingStatus(
    String findingId,
    String status,
  ) async {
    final body = await _client.updateEvaluationFinding(findingId, {
      'status': status,
    });
    return EvaluationFindingDto.fromMap(body);
  }

  Future<ManualEvaluationScoreDto> addManualScore(
    String runId,
    ManualEvaluationScoreRequest request,
  ) async {
    final body = await _client.addManualEvaluationScore(runId, request.toMap());
    return ManualEvaluationScoreDto.fromMap(body);
  }

  Future<List<ManualEvaluationScoreDto>> listManualScores(String runId) async {
    final items = await _client.manualEvaluationScores(runId);
    return items
        .whereType<Map>()
        .map(ManualEvaluationScoreDto.fromMap)
        .toList(growable: false);
  }

  Future<EvaluationReportDto> generateReport(String runId) async {
    final body = await _client.generateEvaluationReport(runId);
    return EvaluationReportDto.fromMap(body);
  }

  Future<List<EvaluationReportDto>> listReports(String runId) async {
    final items = await _client.evaluationReports(runId);
    return items
        .whereType<Map>()
        .map(EvaluationReportDto.fromMap)
        .toList(growable: false);
  }

  Future<EvaluationReportDto> getReport(String reportId) async {
    final body = await _client.evaluationReport(reportId);
    return EvaluationReportDto.fromMap(body);
  }
}

class CreateEvaluationRunRequest {
  const CreateEvaluationRunRequest({
    required this.name,
    required this.targetType,
    required this.targetId,
    this.description,
    this.projectId,
    this.chapterId,
    this.generationId,
    this.revisionId,
    this.adapterEvalSessionId,
    this.memoryRetrievalId,
    this.enabledEvaluators = defaultEvaluationEvaluators,
    this.useLocalModelJudge = false,
    this.localModelId,
    this.context = const {},
    this.runAsync = false,
  });

  final String name;
  final String? description;
  final String targetType;
  final String targetId;
  final String? projectId;
  final String? chapterId;
  final String? generationId;
  final String? revisionId;
  final String? adapterEvalSessionId;
  final String? memoryRetrievalId;
  final List<String> enabledEvaluators;
  final bool useLocalModelJudge;
  final String? localModelId;
  final Map<String, Object?> context;
  final bool runAsync;

  Map<String, Object?> toMap() => {
    'name': name,
    if (description != null && description!.isNotEmpty)
      'description': description,
    'target_type': targetType,
    'target_id': targetId,
    if (projectId != null && projectId!.isNotEmpty) 'project_id': projectId,
    if (chapterId != null && chapterId!.isNotEmpty) 'chapter_id': chapterId,
    if (generationId != null && generationId!.isNotEmpty)
      'generation_id': generationId,
    if (revisionId != null && revisionId!.isNotEmpty) 'revision_id': revisionId,
    if (adapterEvalSessionId != null && adapterEvalSessionId!.isNotEmpty)
      'adapter_eval_session_id': adapterEvalSessionId,
    if (memoryRetrievalId != null && memoryRetrievalId!.isNotEmpty)
      'memory_retrieval_id': memoryRetrievalId,
    'evaluator_config': {
      'enabled_evaluators': enabledEvaluators,
      'use_local_model_judge': useLocalModelJudge,
      if (localModelId != null && localModelId!.isNotEmpty)
        'local_model_id': localModelId,
    },
    if (context.isNotEmpty) 'context': context,
    'run_async': runAsync,
  };
}

class ManualEvaluationScoreRequest {
  const ManualEvaluationScoreRequest({
    this.reviewerId,
    this.overallScore,
    this.dimensions = const {},
    this.notes,
  });

  final String? reviewerId;
  final double? overallScore;
  final Map<String, double> dimensions;
  final String? notes;

  Map<String, Object?> toMap() => {
    if (reviewerId != null && reviewerId!.isNotEmpty) 'reviewer_id': reviewerId,
    if (overallScore != null) 'overall_score': overallScore,
    if (dimensions.isNotEmpty) 'dimensions': dimensions,
    if (notes != null && notes!.isNotEmpty) 'notes': notes,
  };
}
