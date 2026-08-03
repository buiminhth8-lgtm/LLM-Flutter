import 'package:flutter/material.dart';
import 'package:flutter_studio/app/app_routes.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('Novel Studio navigation includes productized workflow entries', (
    tester,
  ) async {
    var selected = -1;
    await tester.binding.setSurfaceSize(const Size(900, 1400));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: buildShellNavigation(
            selectedIndex: novelStudioPageIndex,
            onSelected: (index) => selected = index,
            showNovelStudio: true,
            showPromptStudio: true,
            showContextAssembler: true,
            showWritingWorkspace: true,
            showRevisionReview: true,
            showDatasetBuilder: true,
            showFinetuneCenter: true,
            showAdapterEvaluation: true,
            showMemoryCenter: true,
            showEvaluationCenter: true,
          ),
        ),
      ),
    );

    expect(find.text('小说工作台'), findsOneWidget);
    expect(find.text('项目'), findsOneWidget);
    expect(find.text('评估'), findsOneWidget);

    await tester.tap(find.text('项目'));
    expect(selected, novelProjectsPageIndex);
  });
}
