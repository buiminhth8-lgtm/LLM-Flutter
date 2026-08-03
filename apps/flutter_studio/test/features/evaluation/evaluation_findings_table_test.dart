import 'package:flutter/material.dart';
import 'package:flutter_studio/features/evaluation/models/evaluation_finding_dto.dart';
import 'package:flutter_studio/features/evaluation/widgets/evaluation_findings_table.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('findings table shows finding and changes status', (
    tester,
  ) async {
    String? updatedStatus;
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SizedBox(
            height: 500,
            child: EvaluationFindingsTable(
              findings: const [
                EvaluationFindingDto(
                  findingId: 'finding-1',
                  runId: 'eval-1',
                  severity: 'warning',
                  category: 'plot',
                  title: 'Plot gap',
                  message: 'A goal is not resolved.',
                  status: 'open',
                ),
              ],
              onStatusChanged: (_, status) => updatedStatus = status,
            ),
          ),
        ),
      ),
    );

    expect(find.text('Plot gap'), findsOneWidget);
    await tester.tap(
      find.byKey(const Key('evaluation-finding-status-finding-1')),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.text('resolved').last);
    await tester.pumpAndSettle();
    expect(updatedStatus, 'resolved');
  });
}
