import 'package:flutter/material.dart';
import 'package:flutter_studio/core/ui/app_empty_state.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('AppEmptyState shows title message and action', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: AppEmptyState(
          title: 'Nothing here',
          message: 'Create something first.',
          action: FilledButton(onPressed: () {}, child: const Text('创建')),
        ),
      ),
    );

    expect(find.text('Nothing here'), findsOneWidget);
    expect(find.text('Create something first.'), findsOneWidget);
    expect(find.text('创建'), findsOneWidget);
  });
}
