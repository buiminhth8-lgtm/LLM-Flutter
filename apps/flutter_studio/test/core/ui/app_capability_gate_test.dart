import 'package:flutter/material.dart';
import 'package:flutter_studio/core/ui/app_capability_gate.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('AppCapabilityGate displays child only when exposed', (
    tester,
  ) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: AppCapabilityGate(
          capabilityName: 'novel_studio_product_ui',
          capabilities: [
            {
              'name': 'novel_studio_product_ui',
              'status': 'available',
              'frontend_exposed': true,
            },
          ],
          child: Text('Dashboard ready'),
        ),
      ),
    );

    expect(find.text('Dashboard ready'), findsOneWidget);

    await tester.pumpWidget(
      const MaterialApp(
        home: AppCapabilityGate(
          capabilityName: 'novel_studio_product_ui',
          capabilities: [],
          child: Text('Dashboard ready'),
        ),
      ),
    );

    expect(find.text('能力不可用'), findsOneWidget);
  });
}
