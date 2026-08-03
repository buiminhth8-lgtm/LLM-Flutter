import 'package:flutter/material.dart';
import 'package:flutter_studio/features/evaluation/evaluation_api_client.dart';
import 'package:flutter_studio/features/evaluation/widgets/evaluation_manual_score_panel.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('manual score panel clamps score input to 1-5', (tester) async {
    ManualEvaluationScoreRequest? request;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SingleChildScrollView(
            child: EvaluationManualScorePanel(
              scores: const [],
              onSave: (value) => request = value,
            ),
          ),
        ),
      ),
    );

    await tester.enterText(
      find.byKey(const Key('evaluation-score-overall')),
      '9',
    );
    await tester.enterText(
      find.byKey(const Key('evaluation-manual-notes')),
      'looks good',
    );
    await tester.tap(find.byKey(const Key('evaluation-save-manual-score')));
    await tester.pumpAndSettle();

    expect(request, isNotNull);
    expect(request!.overallScore, 5);
    expect(request!.notes, 'looks good');
  });
}
