import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_studio/main.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class AuthExpiredHttpClient extends http.BaseClient {
  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    final path = request.url.path;
    if (path == '/v1/setup/status') {
      return _json({'requires_setup': false});
    }
    if (path == '/v1/runtime') {
      return _json({
        'error': {'code': 'AUTH_REQUIRED', 'message': 'expired key'},
      }, statusCode: 401);
    }
    return _json({'data': <Object?>[], 'capabilities': <Object?>[]});
  }

  http.StreamedResponse _json(
    Map<String, Object?> body, {
    int statusCode = 200,
  }) {
    return http.StreamedResponse(
      Stream.value(utf8.encode(jsonEncode(body))),
      statusCode,
      headers: {'content-type': 'application/json'},
    );
  }
}

void main() {
  testWidgets('LLM Studio shell renders grouped primary navigation', (
    tester,
  ) async {
    await tester.pumpWidget(const LlmStudioApp(autoRefresh: false));

    expect(find.text('LLM Studio'), findsOneWidget);
    expect(find.text('核心'), findsOneWidget);
    expect(find.text('工作流'), findsOneWidget);
    expect(find.text('状态'), findsOneWidget);
    expect(find.text('模型'), findsWidgets);
    expect(find.text('聊天'), findsOneWidget);
    expect(find.text('小说工作台'), findsNothing);
  });

  testWidgets('first run setup state shows initialization page', (
    tester,
  ) async {
    await tester.pumpWidget(
      const LlmStudioApp(autoRefresh: false, initialRequiresSetup: true),
    );

    expect(find.text('初始化 LLM Studio'), findsOneWidget);
    expect(find.text('管理员密码'), findsOneWidget);
    expect(find.text('确认管理员密码'), findsOneWidget);
    expect(find.text('初始化'), findsOneWidget);
    expect(find.text('设置'), findsNothing);
  });

  testWidgets('chat is disabled until a model is loaded', (tester) async {
    await tester.pumpWidget(const LlmStudioApp(autoRefresh: false));
    await tester.tap(find.text('聊天'));
    await tester.pumpAndSettle();

    expect(find.text('请先在模型页面加载模型。'), findsOneWidget);
    final sendButton = tester.widget<FilledButton>(
      find.widgetWithText(FilledButton, '发送'),
    );
    expect(sendButton.onPressed, isNull);
  });

  testWidgets('settings exposes clear auth and backend logs', (tester) async {
    await tester.binding.setSurfaceSize(const Size(1100, 1400));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    await tester.pumpWidget(const LlmStudioApp(autoRefresh: false));
    await tester.drag(find.byType(ListView).first, const Offset(0, -500));
    await tester.pumpAndSettle();
    final settingsNav = find.widgetWithText(ListTile, '设置');
    await tester.ensureVisible(settingsNav);
    await tester.tap(settingsNav);
    await tester.pumpAndSettle();

    expect(find.text('清除认证'), findsOneWidget);
    await tester.ensureVisible(find.text('后端日志'));

    expect(find.text('后端日志'), findsOneWidget);
    expect(find.text('复制日志'), findsOneWidget);
    await tester.ensureVisible(find.text('小说工作台路线图'));
    expect(find.text('小说工作台路线图'), findsOneWidget);
    expect(find.text('状态：已规划 / 未实现。'), findsOneWidget);
  });

  testWidgets('401 responses return the user to the auth settings page', (
    tester,
  ) async {
    SharedPreferences.setMockInitialValues({
      'llm_studio.api_key': 'expired-key',
      'llm_studio.backend_mode': 'remote',
      'llm_studio.auto_start_backend': false,
    });
    final client = LlmStudioClient(
      'http://127.0.0.1:8000',
      httpClient: AuthExpiredHttpClient(),
    );

    await tester.pumpWidget(LlmStudioApp(client: client));
    await tester.pumpAndSettle();

    await tester.ensureVisible(find.text('连接设置'));
    expect(find.text('连接设置'), findsOneWidget);
    expect(find.text('清除认证'), findsOneWidget);
    expect(find.text('认证已失效，请重新登录或填写有效 API Key。'), findsOneWidget);
  });
}
