import 'package:flutter/material.dart';
import 'package:flutter_studio/features/evaluation/evaluation_api_client.dart';
import 'package:flutter_studio/features/evaluation/widgets/evaluation_create_run_dialog.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('create run dialog builds a request with selected evaluators', (
    tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(900, 1000));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    CreateEvaluationRunRequest? request;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: EvaluationCreateRunDialog(
            initialTargetType: 'revision',
            initialTargetId: 'rev-1',
            onCreate: (value) => request = value,
          ),
        ),
      ),
    );

    await tester.enterText(
      find.byKey(const Key('evaluation-run-name')),
      'Review run',
    );
    await tester.tap(find.byKey(const Key('evaluation-local-model-judge')));
    await tester.pumpAndSettle();
    await tester.enterText(
      find.byKey(const Key('evaluation-local-model-id')),
      'judge-local',
    );
    await tester.tap(find.byKey(const Key('evaluation-create-run-submit')));
    await tester.pumpAndSettle();

    expect(request, isNotNull);
    expect(request!.targetType, 'revision');
    expect(request!.targetId, 'rev-1');
    expect(request!.useLocalModelJudge, isTrue);
    expect(request!.toMap()['evaluator_config'], isA<Map>());
  });
}
