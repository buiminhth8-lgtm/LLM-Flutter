import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_studio/main.dart';

void main() {
  testWidgets('LLM Studio shell renders primary navigation', (tester) async {
    await tester.pumpWidget(const LlmStudioApp(autoRefresh: false));

    expect(find.text('LLM Studio'), findsOneWidget);
    expect(find.text('Status'), findsOneWidget);
    expect(find.text('Models'), findsWidgets);
    expect(find.text('Chat'), findsOneWidget);
    expect(find.text('Settings'), findsOneWidget);
  });

  testWidgets('first run setup state shows initialization page', (
    tester,
  ) async {
    await tester.pumpWidget(
      const LlmStudioApp(autoRefresh: false, initialRequiresSetup: true),
    );

    expect(find.text('初始化 LLM-Studio'), findsOneWidget);
    expect(find.text('管理员密码'), findsOneWidget);
    expect(find.text('确认管理员密码'), findsOneWidget);
    expect(find.text('初始化'), findsOneWidget);
    expect(find.text('Settings'), findsNothing);
  });

  testWidgets('chat is disabled until a model is loaded', (tester) async {
    await tester.pumpWidget(const LlmStudioApp(autoRefresh: false));
    await tester.tap(find.text('Chat'));
    await tester.pumpAndSettle();

    expect(
      find.text('Please load a model on the Models page.'),
      findsOneWidget,
    );
    final sendButton = tester.widget<FilledButton>(
      find.widgetWithText(FilledButton, 'Send'),
    );
    expect(sendButton.onPressed, isNull);
  });

  testWidgets('settings exposes clear auth and backend logs', (tester) async {
    await tester.pumpWidget(const LlmStudioApp(autoRefresh: false));
    await tester.tap(find.text('Settings'));
    await tester.pumpAndSettle();

    expect(find.text('Clear auth'), findsOneWidget);
    await tester.drag(find.byType(ListView).last, const Offset(0, -400));
    await tester.pumpAndSettle();

    expect(find.text('Backend logs'), findsOneWidget);
    expect(find.text('Copy logs'), findsOneWidget);
  });
}
