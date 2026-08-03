import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_studio/app/app_routes.dart';
import 'package:flutter_studio/core/api/api_client.dart';
import 'package:flutter_studio/features/prompt_studio/models/prompt_render_result_dto.dart';
import 'package:flutter_studio/features/prompt_studio/models/prompt_template_dto.dart';
import 'package:flutter_studio/features/prompt_studio/prompt_api_client.dart';
import 'package:flutter_studio/features/prompt_studio/prompt_controller.dart';
import 'package:flutter_studio/features/prompt_studio/prompt_state.dart';
import 'package:flutter_studio/features/prompt_studio/prompt_studio_page.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

Widget _wrap(Widget child) => MaterialApp(home: Scaffold(body: child));

class PromptPageHttpClient extends http.BaseClient {
  String lastPostBody = '';

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    if (request is http.Request && request.method == 'POST') {
      lastPostBody = request.body;
    }
    Object responseBody = {'data': <Object?>[]};
    if (request.url.path == '/v1/prompts/templates' &&
        request.method == 'POST') {
      responseBody = {
        'id': 'template-1',
        'name': 'Template',
        'type': 'chapter_generate',
        'scope': 'global',
        'status': 'active',
      };
    }
    return http.StreamedResponse(
      Stream.value(utf8.encode(jsonEncode(responseBody))),
      200,
      headers: {'content-type': 'application/json'},
    );
  }
}

void main() {
  testWidgets('prompt_studio capability controls navigation', (tester) async {
    await tester.pumpWidget(
      _wrap(
        buildShellNavigation(
          selectedIndex: 0,
          onSelected: (_) {},
          showNovelStudio: true,
          showPromptStudio: false,
        ),
      ),
    );
    expect(find.text('提示词工作室'), findsNothing);

    await tester.pumpWidget(
      _wrap(
        buildShellNavigation(
          selectedIndex: promptStudioPageIndex,
          onSelected: (_) {},
          showNovelStudio: true,
          showPromptStudio: true,
        ),
      ),
    );
    expect(find.text('提示词工作室', skipOffstage: false), findsOneWidget);
  });

  testWidgets('create template form submits and invalid JSON disables save', (
    tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(1400, 900));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    final httpClient = PromptPageHttpClient();
    final controller = PromptController(
      PromptApiClient(
        LlmStudioClient('http://127.0.0.1:8000', httpClient: httpClient),
      ),
    );

    await tester.pumpWidget(_wrap(PromptStudioPage(controller: controller)));
    await tester.enterText(find.widgetWithText(TextField, '变量结构 JSON'), '{bad');
    await tester.pump();
    expect(
      tester
          .widget<FilledButton>(find.widgetWithText(FilledButton, '创建模板'))
          .onPressed,
      isNull,
    );

    await tester.enterText(
      find.widgetWithText(TextField, '变量结构 JSON'),
      '{"project_title":{"type":"string","required":true}}',
    );
    await tester.pump();
    expect(
      tester
          .widget<FilledButton>(find.widgetWithText(FilledButton, '创建模板'))
          .onPressed,
      isNotNull,
    );
  });

  testWidgets('render preview shows rendered prompt and missing variables', (
    tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(1400, 900));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    final controller = PromptController(
      PromptApiClient(LlmStudioClient('http://127.0.0.1:8000')),
    );
    controller.state = const PromptState(
      templates: [
        PromptTemplateDto(
          id: 'template-1',
          name: 'Template',
          type: 'chapter_generate',
          scope: 'global',
          status: 'active',
          activeVersionId: 'version-1',
        ),
      ],
      selectedTemplateId: 'template-1',
      renderResult: PromptRenderResultDto(
        templateId: 'template-1',
        templateVersionId: 'version-1',
        renderedPrompt: '已渲染提示词',
        missingVariables: ['chapter_outline'],
        warnings: [],
        promptHash: 'abc',
      ),
    );

    await tester.pumpWidget(_wrap(PromptStudioPage(controller: controller)));

    expect(find.text('已渲染提示词'), findsWidgets);
    expect(find.text('缺失变量：chapter_outline'), findsOneWidget);
    expect(find.text('提示词哈希：abc'), findsOneWidget);
  });
}
