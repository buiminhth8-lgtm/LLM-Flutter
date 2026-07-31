import 'package:flutter/material.dart';
import 'package:flutter_studio/features/revisions/widgets/revision_score_selector.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('Score Selector only offers one to five', (tester) async {
    int? selected;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: RevisionScoreSelector(
            value: selected,
            onChanged: (value) => selected = value,
          ),
        ),
      ),
    );

    await tester.tap(find.byKey(const Key('revision-score-selector')));
    await tester.pumpAndSettle();

    expect(find.text('1 很差'), findsOneWidget);
    expect(find.text('5 很好'), findsOneWidget);
    expect(find.text('6'), findsNothing);
  });
}
