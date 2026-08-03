import 'package:flutter/material.dart';
import 'package:flutter_studio/features/adapter_evaluation/models/adapter_eval_score_dto.dart';
import 'package:flutter_studio/features/adapter_evaluation/widgets/adapter_score_panel.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('Score panel saves manual scores from 1 to 5', (tester) async {
    AdapterEvalScoreRequest? saved;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: AdapterScorePanel(
            initialScore: AdapterEvalScoreDto.fromMap({
              'score_id': 'score-1',
              'case_id': 'case-1',
              'session_id': 'session-1',
              'winner': 'base',
              'base_score': 2,
              'adapter_score': 4,
              'dimensions': const {},
            }),
            onSave: (request) => saved = request,
          ),
        ),
      ),
    );

    expect(find.text('2'), findsOneWidget);
    expect(find.text('4'), findsOneWidget);
    await tester.tap(find.byKey(const Key('adapter-eval-save-score')));
    await tester.pump();

    expect(saved, isNotNull);
    expect(saved!.winner, 'base');
    expect(saved!.baseScore, inInclusiveRange(1, 5));
    expect(saved!.adapterScore, inInclusiveRange(1, 5));
  });
}
