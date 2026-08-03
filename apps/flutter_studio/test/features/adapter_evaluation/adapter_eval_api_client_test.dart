import 'dart:convert';

import 'package:flutter_studio/core/api/api_client.dart';
import 'package:flutter_studio/features/adapter_evaluation/adapter_eval_api_client.dart';
import 'package:flutter_studio/features/adapter_evaluation/models/adapter_eval_create_request_dto.dart';
import 'package:flutter_studio/features/adapter_evaluation/models/adapter_eval_score_dto.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

class AdapterEvalApiHttpClient extends http.BaseClient {
  final List<String> paths = [];
  bool sessionCreated = false;
  bool caseCreated = false;
  bool scored = false;
  bool revisionCreated = false;

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    final path = request.url.path;
    paths.add('${request.method} $path');
    Object response = _session(includeCases: true);
    if (path == '/v1/adapter-evaluations/sessions') {
      if (request.method == 'POST') {
        sessionCreated = true;
        response = _session(includeCases: true);
      } else {
        response = {
          'data': [_session()],
        };
      }
    } else if (path.endsWith('/cases') && request.method == 'POST') {
      caseCreated = true;
      response = _case(includeResults: false);
    } else if (path.endsWith('/prepare')) {
      response = _case();
    } else if (path.endsWith('/run')) {
      response = path.contains('/sessions/')
          ? _session(includeCases: true)
          : _case(includeResults: true);
    } else if (path.endsWith('/score')) {
      scored = true;
      response = _score();
    } else if (path.endsWith('/report') && request.method == 'POST') {
      response = _report();
    } else if (path.endsWith('/reports') && request.method == 'GET') {
      response = {
        'data': [_report()],
      };
    } else if (path.endsWith('/create-revision')) {
      revisionCreated = true;
      response = _revision();
    } else if (path == '/v1/adapter-evaluations/cases/case-1') {
      response = _case(includeResults: true, includeScore: true);
    }
    return http.StreamedResponse(
      Stream.value(utf8.encode(jsonEncode(response))),
      200,
      headers: {'content-type': 'application/json'},
    );
  }

  Map<String, Object?> _session({bool includeCases = false}) => {
    'session_id': 'session-1',
    'name': '适配器评估',
    'project_id': 'project-1',
    'dataset_version_id': 'dsv-1',
    'finetune_run_id': 'run-1',
    'base_model_id': 'qwen-local',
    'adapter_id': 'adapter-1',
    'status': 'reviewing',
    'stats': {'case_count': 1},
    if (includeCases) 'cases': [_case(includeResults: true)],
    'reports': [_report()],
  };

  Map<String, Object?> _case({
    bool includeResults = true,
    bool includeScore = false,
  }) => {
    'case_id': 'case-1',
    'session_id': 'session-1',
    'title': 'Case 1',
    'project_id': 'project-1',
    'chapter_id': 'chapter-1',
    'template_id': 'template-1',
    'mode': 'chapter_continue',
    'status': 'completed',
    'prompt_rendered': 'prompt',
    'context_snapshot': {'project': 'p'},
    'generation_params': {'max_tokens': 128},
    'target_length': {'unit': 'chars'},
    if (includeResults) 'results': [_result('base'), _result('adapter')],
    if (includeScore) 'score': _score(),
  };

  Map<String, Object?> _result(String variant) => {
    'result_id': 'result-$variant',
    'case_id': 'case-1',
    'session_id': 'session-1',
    'variant': variant,
    'model_id': 'qwen-local',
    'adapter_id': variant == 'adapter' ? 'adapter-1' : null,
    'status': 'succeeded',
    'output_text': '$variant output',
    'finish_reason': 'stop',
    'output_char_count': 11,
    'output_token_estimate': 4,
  };

  Map<String, Object?> _score() => {
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
  };

  Map<String, Object?> _report() => {
    'report_id': 'report-1',
    'session_id': 'session-1',
    'report': {
      'adapter_win_count': 1,
      'base_win_count': 0,
      'average_base_score': 3,
      'average_adapter_score': 5,
      'recommendation': 'adapter_candidate',
    },
    'summary_text': 'Adapter is better on the manually scored cases.',
  };

  Map<String, Object?> _revision() => {
    'revision_id': 'rev-1',
    'project_id': 'project-1',
    'chapter_id': 'chapter-1',
    'original_text': 'base output',
    'edited_text': 'adapter output',
    'diff': {
      'summary': {'changed_blocks': 1},
      'ops': [
        {'type': 'delete', 'text': 'base'},
        {'type': 'insert', 'text': 'adapter'},
      ],
    },
    'edit_tags': ['style_unify'],
    'status': 'draft',
    'accepted_for_dataset': false,
    'source': 'adapter_evaluation',
    'original_hash': 'oh',
    'edited_hash': 'eh',
    'created_at': 'now',
    'updated_at': 'now',
  };
}

void main() {
  test(
    'AdapterEvalApiClient parses DTOs and calls stage 9 endpoints',
    () async {
      final httpClient = AdapterEvalApiHttpClient();
      final api = AdapterEvalApiClient(
        LlmStudioClient('http://127.0.0.1:8000', httpClient: httpClient),
      );

      final session = await api.createSession(
        const CreateAdapterEvalSessionRequest(
          name: '适配器评估',
          baseModelId: 'qwen-local',
          adapterId: 'adapter-1',
          finetuneRunId: 'run-1',
        ),
      );
      final sessions = await api.listSessions();
      final detail = await api.getSession('session-1');
      final createdCase = await api.createCase(
        'session-1',
        const CreateAdapterEvalCaseRequest(
          title: 'Case 1',
          templateId: 'template-1',
          mode: 'chapter_continue',
          projectId: 'project-1',
        ),
      );
      final caseDto = await api.getCase('case-1');
      final prepared = await api.prepareCase('case-1');
      final runCase = await api.runCase('case-1');
      final runSession = await api.runSession('session-1');
      final score = await api.scoreCase(
        'case-1',
        const AdapterEvalScoreRequest(
          winner: 'adapter',
          baseScore: 3,
          adapterScore: 5,
        ),
      );
      final report = await api.generateReport('session-1');
      final reports = await api.listReports('session-1');
      final revision = await api.createRevisionFromEvalResult(
        'result-adapter',
        const CreateRevisionFromEvalResultRequest(projectId: 'project-1'),
      );

      expect(session.sessionId, 'session-1');
      expect(sessions.single.adapterId, 'adapter-1');
      expect(detail.cases.single.results.length, 2);
      expect(createdCase.caseId, 'case-1');
      expect(caseDto.score?.winner, 'adapter');
      expect(prepared.status, 'completed');
      expect(runCase.results.last.outputText, 'adapter output');
      expect(runSession.sessionId, 'session-1');
      expect(score.adapterScore, 5);
      expect(report.recommendation, 'adapter_candidate');
      expect(reports.single.reportId, 'report-1');
      expect(revision.source, 'adapter_evaluation');
      expect(httpClient.sessionCreated, isTrue);
      expect(httpClient.caseCreated, isTrue);
      expect(httpClient.scored, isTrue);
      expect(httpClient.revisionCreated, isTrue);
    },
  );
}
