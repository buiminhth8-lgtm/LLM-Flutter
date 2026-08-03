import 'package:flutter/material.dart';
import 'package:flutter_studio/features/evaluation/models/evaluation_report_dto.dart';
import 'package:flutter_studio/features/evaluation/widgets/evaluation_report_panel.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('report panel displays summary and triggers generation', (
    tester,
  ) async {
    var generated = false;
    String? openedReport;
    const report = EvaluationReportDto(
      reportId: 'report-1',
      runId: 'eval-1',
      reportType: 'chapter_evaluation',
      summaryText: 'Novel evaluation report',
      report: {
        'summary': {'overall_score': 4.1},
        'metrics': [],
        'findings': [],
        'manual_evaluation': [],
        'limitations': ['advisory only'],
      },
    );
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SizedBox(
            height: 700,
            child: EvaluationReportPanel(
              reports: const [report],
              currentReport: report,
              onGenerate: () => generated = true,
              onOpenReport: (value) => openedReport = value,
            ),
          ),
        ),
      ),
    );

    expect(find.text('Novel evaluation report'), findsWidgets);
    await tester.tap(find.byKey(const Key('evaluation-generate-report')));
    await tester.pumpAndSettle();
    expect(generated, isTrue);
    await tester.tap(find.byKey(const Key('evaluation-report-report-1')));
    await tester.pumpAndSettle();
    expect(openedReport, 'report-1');
  });
}
