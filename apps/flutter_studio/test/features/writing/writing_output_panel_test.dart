import 'package:flutter/material.dart';
import 'package:flutter_studio/features/writing/widgets/writing_output_panel.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('output panel shows streamed text and draft actions', (
    tester,
  ) async {
    var stopped = false;
    var saved = false;
    var appended = false;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SizedBox(
            height: 500,
            child: WritingOutputPanel(
              output: '夜色沉入旧城。',
              generating: true,
              saving: false,
              canSave: true,
              onStop: () => stopped = true,
              onSave: () => saved = true,
              onAppend: () => appended = true,
            ),
          ),
        ),
      ),
    );

    expect(find.text('夜色沉入旧城。'), findsOneWidget);
    await tester.tap(find.byKey(const Key('writing-stop')));
    await tester.tap(find.byKey(const Key('writing-save-draft')));
    await tester.tap(find.byKey(const Key('writing-append-draft')));
    expect(stopped, isTrue);
    expect(saved, isTrue);
    expect(appended, isTrue);
    expect(find.textContaining('阶段 5'), findsOneWidget);
  });
}
