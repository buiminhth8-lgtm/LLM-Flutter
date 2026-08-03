import 'package:flutter_studio/features/adapter_evaluation/adapter_eval_state.dart';
import 'package:flutter_studio/features/adapter_evaluation/models/adapter_eval_case_dto.dart';
import 'package:flutter_studio/features/adapter_evaluation/models/adapter_eval_report_dto.dart';
import 'package:flutter_studio/features/adapter_evaluation/models/adapter_eval_result_dto.dart';
import 'package:flutter_studio/features/adapter_evaluation/models/adapter_eval_score_dto.dart';
import 'package:flutter_studio/features/adapter_evaluation/models/adapter_eval_session_dto.dart';

AdapterEvalResultDto adapterEvalResult(String variant) =>
    AdapterEvalResultDto.fromMap({
      'result_id': 'result-$variant',
      'case_id': 'case-1',
      'session_id': 'session-1',
      'variant': variant,
      'model_id': 'qwen-local',
      'adapter_id': variant == 'adapter' ? 'adapter-1' : null,
      'status': 'succeeded',
      'output_text': '$variant output',
      'finish_reason': 'stop',
      'output_char_count': 12,
      'output_token_estimate': 4,
    });

AdapterEvalScoreDto adapterEvalScore() => AdapterEvalScoreDto.fromMap({
  'score_id': 'score-1',
  'case_id': 'case-1',
  'session_id': 'session-1',
  'base_result_id': 'result-base',
  'adapter_result_id': 'result-adapter',
  'winner': 'adapter',
  'base_score': 3,
  'adapter_score': 5,
  'dimensions': {
    'style': {'base': 3, 'adapter': 5},
  },
  'notes': 'Adapter better.',
});

AdapterEvalCaseDto adapterEvalCase({bool withScore = true}) =>
    AdapterEvalCaseDto(
      caseId: 'case-1',
      sessionId: 'session-1',
      title: 'Opening continuation',
      mode: 'chapter_continue',
      status: 'completed',
      projectId: 'project-1',
      chapterId: 'chapter-1',
      templateId: 'template-1',
      promptRendered: 'Frozen prompt',
      contextSnapshot: const {'project': 'p'},
      generationParams: const {'max_tokens': 128},
      targetLength: const {'unit': 'chars', 'max': 500},
      results: [adapterEvalResult('base'), adapterEvalResult('adapter')],
      score: withScore ? adapterEvalScore() : null,
    );

AdapterEvalReportDto adapterEvalReport() => AdapterEvalReportDto.fromMap({
  'report_id': 'report-1',
  'session_id': 'session-1',
  'report': {
    'adapter_win_count': 1,
    'base_win_count': 0,
    'average_base_score': 3,
    'average_adapter_score': 5,
    'recommendation': 'adapter_candidate',
  },
  'summary_text': 'Adapter is better on manually scored cases.',
});

AdapterEvalSessionDto adapterEvalSession() => AdapterEvalSessionDto(
  sessionId: 'session-1',
  name: '适配器对比',
  projectId: 'project-1',
  finetuneRunId: 'run-1',
  datasetVersionId: 'dsv-1',
  baseModelId: 'qwen-local',
  adapterId: 'adapter-1',
  status: 'reviewing',
  cases: [adapterEvalCase()],
  reports: [adapterEvalReport()],
  stats: const {'case_count': 1},
);

AdapterEvalState adapterEvalState() => AdapterEvalState(
  sessions: [adapterEvalSession()],
  currentSession: adapterEvalSession(),
  currentCase: adapterEvalCase(),
  reports: [adapterEvalReport()],
);
