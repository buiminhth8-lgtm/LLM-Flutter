import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_studio/app/app_routes.dart';
import 'package:flutter_studio/core/api/api_client.dart';
import 'package:flutter_studio/features/evaluation/evaluation_api_client.dart';
import 'package:flutter_studio/features/evaluation/evaluation_center_page.dart';
import 'package:flutter_studio/features/evaluation/evaluation_controller.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

class EvaluationCenterHttpClient extends http.BaseClient {
  bool created = false;

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    Object body = _run();
    if (request.url.path == '/v1/evaluation/runs' && request.method == 'GET') {
      body = {
        'data': [_run()],
      };
    } else if (request.url.path == '/v1/evaluation/runs' &&
        request.method == 'POST') {
      created = true;
      body = _run(name: 'Created run');
    } else if (request.url.path.endsWith('/metrics') ||
        request.url.path.endsWith('/findings') ||
        request.url.path.endsWith('/manual-scores') ||
        request.url.path.endsWith('/reports')) {
      body = {'data': <Object?>[]};
    }
    return http.StreamedResponse(
      Stream.value(utf8.encode(jsonEncode(body))),
      200,
      headers: {'content-type': 'application/json'},
    );
  }

  Map<String, Object?> _run({String name = 'Chapter evaluation'}) => {
    'run_id': 'eval-1',
    'name': name,
    'target_type': 'chapter',
    'target_id': 'c1',
    'status': 'completed',
    'evaluator_config': {
      'enabled_evaluators': ['repetition'],
    },
    'overall_score': 4,
  };
}

void main() {
  testWidgets('Evaluation Center lists runs and creates a new run', (
    tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(1500, 1000));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    final httpClient = EvaluationCenterHttpClient();
    final controller = EvaluationController(
      EvaluationApiClient(
        LlmStudioClient('http://127.0.0.1:8000', httpClient: httpClient),
      ),
    );
    addTearDown(controller.dispose);
    await controller.refresh();

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: EvaluationCenterPage(controller: controller)),
      ),
    );

    expect(find.text('Chapter evaluation'), findsOneWidget);
    await tester.tap(find.byKey(const Key('evaluation-new-run')));
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const Key('evaluation-target-id')), 'c1');
    await tester.tap(find.byKey(const Key('evaluation-create-run-submit')));
    await tester.pumpAndSettle();
    expect(httpClient.created, isTrue);
  });

  testWidgets('full_evaluation_center capability controls navigation entry', (
    tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(900, 1400));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: buildShellNavigation(
            selectedIndex: 0,
            onSelected: (_) {},
            showNovelStudio: true,
            showEvaluationCenter: false,
          ),
        ),
      ),
    );
    expect(find.text('Evaluation'), findsNothing);

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: buildShellNavigation(
            selectedIndex: 0,
            onSelected: (_) {},
            showNovelStudio: true,
            showEvaluationCenter: true,
          ),
        ),
      ),
    );
    expect(find.text('Evaluation'), findsOneWidget);
  });
}
