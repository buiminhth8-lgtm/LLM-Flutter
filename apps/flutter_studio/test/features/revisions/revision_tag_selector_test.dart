import 'package:flutter/material.dart';
import 'package:flutter_studio/features/revisions/widgets/revision_tag_selector.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('Tag Selector can select multiple tags', (tester) async {
    var values = <String>[];
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: StatefulBuilder(
            builder: (context, setState) => RevisionTagSelector(
              values: values,
              onChanged: (next) => setState(() => values = next),
            ),
          ),
        ),
      ),
    );

    await tester.tap(find.byKey(const Key('revision-tag-language_polish')));
    await tester.pump();
    await tester.tap(find.byKey(const Key('revision-tag-detail_expand')));
    await tester.pump();

    expect(values, containsAll(['language_polish', 'detail_expand']));
  });
}
