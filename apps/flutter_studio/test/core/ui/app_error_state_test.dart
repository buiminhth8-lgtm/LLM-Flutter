import 'package:flutter/material.dart';
import 'package:flutter_studio/core/ui/app_error_state.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('AppErrorState shows retry action', (tester) async {
    var retried = false;
    await tester.pumpWidget(
      MaterialApp(
        home: AppErrorState(
          message: 'Backend failed',
          onRetry: () => retried = true,
        ),
      ),
    );

    expect(find.text('Backend failed'), findsOneWidget);
    await tester.tap(find.byIcon(Icons.refresh));
    expect(retried, isTrue);
  });
}
