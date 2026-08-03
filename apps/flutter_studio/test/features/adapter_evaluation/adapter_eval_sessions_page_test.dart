import 'package:flutter/material.dart';
import 'package:flutter_studio/app/app_routes.dart';
import 'package:flutter_studio/core/api/api_client.dart';
import 'package:flutter_studio/features/adapter_evaluation/adapter_eval_api_client.dart';
import 'package:flutter_studio/features/adapter_evaluation/adapter_eval_controller.dart';
import 'package:flutter_studio/features/adapter_evaluation/adapter_eval_sessions_page.dart';
import 'package:flutter_test/flutter_test.dart';

import 'adapter_eval_widget_fixtures.dart';

void main() {
  testWidgets('Adapter Evaluation sessions page displays list and detail', (
    tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(1500, 1000));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    final controller = AdapterEvalController(
      AdapterEvalApiClient(LlmStudioClient('http://localhost')),
    );
    addTearDown(controller.dispose);
    controller.state = adapterEvalState();

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: AdapterEvalSessionsPage(controller: controller)),
      ),
    );

    expect(find.text('适配器评估'), findsOneWidget);
    expect(find.text('适配器对比'), findsWidgets);
    expect(find.text('Opening continuation'), findsWidgets);
    expect(find.text('base output'), findsOneWidget);
    expect(find.text('adapter output'), findsOneWidget);
    expect(find.byKey(const Key('adapter-eval-new-session')), findsOneWidget);
  });

  testWidgets('adapter_evaluation capability flag controls navigation entry', (
    tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(900, 1200));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: buildShellNavigation(
            selectedIndex: 0,
            onSelected: (_) {},
            showNovelStudio: true,
            showAdapterEvaluation: false,
          ),
        ),
      ),
    );
    expect(find.text('适配器评估'), findsNothing);

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: buildShellNavigation(
            selectedIndex: 0,
            onSelected: (_) {},
            showNovelStudio: true,
            showAdapterEvaluation: true,
          ),
        ),
      ),
    );
    expect(find.text('适配器评估'), findsOneWidget);
  });
}
