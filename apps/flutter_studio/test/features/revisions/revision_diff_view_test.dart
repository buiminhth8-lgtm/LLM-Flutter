import 'package:flutter/material.dart';
import 'package:flutter_studio/features/revisions/models/revision_diff_dto.dart';
import 'package:flutter_studio/features/revisions/widgets/revision_diff_view.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('Diff View shows summary and insert/delete markers', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SizedBox(
            width: 700,
            height: 500,
            child: RevisionDiffView(
              diff: RevisionDiffDto.fromMap({
                'summary': {
                  'original_chars': 10,
                  'edited_chars': 12,
                  'added_chars': 4,
                  'removed_chars': 2,
                  'changed_blocks': 1,
                },
                'ops': [
                  {'type': 'equal', 'text': 'same'},
                  {'type': 'delete', 'text': 'old'},
                  {'type': 'insert', 'text': 'new'},
                ],
              }),
            ),
          ),
        ),
      ),
    );

    expect(find.text('区块: 1'), findsOneWidget);
    expect(find.text('- old'), findsOneWidget);
    expect(find.text('+ new'), findsOneWidget);
  });
}
