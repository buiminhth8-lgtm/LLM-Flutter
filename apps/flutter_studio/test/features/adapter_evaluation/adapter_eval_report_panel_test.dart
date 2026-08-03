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

      expect(find.text('评估报告'), findsOneWidget);
      expect(find.text('适配器胜出次数：1'), findsOneWidget);
      expect(find.text('基础模型胜出次数：0'), findsOneWidget);
      expect(find.text('建议：adapter_candidate'), findsOneWidget);
    },
  );
}
