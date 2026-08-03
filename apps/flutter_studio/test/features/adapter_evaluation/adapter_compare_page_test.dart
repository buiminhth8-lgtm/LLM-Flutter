import 'package:flutter/material.dart';
import 'package:flutter_studio/core/api/api_client.dart';
import 'package:flutter_studio/features/adapter_evaluation/adapter_compare_page.dart';
import 'package:flutter_studio/features/adapter_evaluation/adapter_eval_api_client.dart';
import 'package:flutter_studio/features/adapter_evaluation/adapter_eval_controller.dart';
import 'package:flutter_test/flutter_test.dart';

import 'adapter_eval_widget_fixtures.dart';

void main() {
  testWidgets('Compare page displays base and adapter outputs', (tester) async {
    await tester.binding.setSurfaceSize(const Size(1200, 1200));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    final controller = AdapterEvalController(
      AdapterEvalApiClient(LlmStudioClient('http://localhost')),
    );
    addTearDown(controller.dispose);
    controller.state = adapterEvalState();

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: AdapterComparePage(controller: controller)),
      ),
    );

    expect(find.byKey(const Key('adapter-compare-page')), findsOneWidget);
    expect(find.text('base output'), findsOneWidget);
    expect(find.text('adapter output'), findsOneWidget);
    expect(find.byKey(const Key('adapter-eval-run-case')), findsOneWidget);
    expect(find.byKey(const Key('adapter-eval-save-score')), findsOneWidget);
    expect(
      find.byKey(const Key('adapter-eval-create-revision-adapter')),
      findsOneWidget,
    );
    await tester.tap(find.text('提示词 / 上下文快照'));
    await tester.pumpAndSettle();
    expect(find.text('Frozen prompt'), findsOneWidget);
  });
}
