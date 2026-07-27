import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_studio/main.dart';

void main() {
  testWidgets('LLM Studio shell renders primary navigation', (tester) async {
    await tester.pumpWidget(const LlmStudioApp(autoRefresh: false));

    expect(find.text('LLM Studio'), findsOneWidget);
    expect(find.text('Status'), findsOneWidget);
    expect(find.text('Models'), findsOneWidget);
    expect(find.text('Chat'), findsOneWidget);
    expect(find.text('Settings'), findsOneWidget);
  });
}
