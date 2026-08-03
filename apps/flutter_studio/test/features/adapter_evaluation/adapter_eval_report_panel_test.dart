import 'package:flutter/material.dart';
import 'package:flutter_studio/features/adapter_evaluation/widgets/adapter_eval_report_panel.dart';
import 'package:flutter_test/flutter_test.dart';

import 'adapter_eval_widget_fixtures.dart';

void main() {
  testWidgets(
    'Report panel displays manual scoring summary and recommendation',
    (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AdapterEvalReportPanel(reports: [adapterEvalReport()]),
          ),
        ),
      );

      expect(find.text('Evaluation Report'), findsOneWidget);
      expect(find.text('adapter_win_count: 1'), findsOneWidget);
      expect(find.text('base_win_count: 0'), findsOneWidget);
      expect(find.text('recommendation: adapter_candidate'), findsOneWidget);
    },
  );
}
