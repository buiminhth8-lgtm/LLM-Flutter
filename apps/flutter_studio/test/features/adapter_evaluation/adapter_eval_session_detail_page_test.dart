import 'package:flutter/material.dart';
import 'package:flutter_studio/core/api/api_client.dart';
import 'package:flutter_studio/features/adapter_evaluation/adapter_eval_api_client.dart';
import 'package:flutter_studio/features/adapter_evaluation/adapter_eval_controller.dart';
import 'package:flutter_studio/features/adapter_evaluation/adapter_eval_session_detail_page.dart';
import 'package:flutter_test/flutter_test.dart';

import 'adapter_eval_widget_fixtures.dart';

void main() {
  testWidgets('Session detail page shows cases, controls and report', (
    tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(1000, 1000));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    final controller = AdapterEvalController(
      AdapterEvalApiClient(LlmStudioClient('http://localhost')),
    );
    addTearDown(controller.dispose);
    controller.state = adapterEvalState();

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: AdapterEvalSessionDetailPage(controller: controller),
        ),
      ),
    );

    expect(
      find.byKey(const Key('adapter-eval-session-detail')),
      findsOneWidget,
    );
    expect(find.text('base_model_id: qwen-local'), findsOneWidget);
    expect(find.byKey(const Key('adapter-eval-add-case')), findsOneWidget);
    expect(find.byKey(const Key('adapter-eval-run-session')), findsOneWidget);
    expect(
      find.byKey(const Key('adapter-eval-generate-report')),
      findsOneWidget,
    );
    expect(find.text('Opening continuation'), findsOneWidget);
    expect(find.text('recommendation: adapter_candidate'), findsOneWidget);
  });
}
