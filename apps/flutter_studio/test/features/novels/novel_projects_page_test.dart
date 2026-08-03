import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_studio/app/app_routes.dart';
import 'package:flutter_studio/core/api/api_client.dart';
import 'package:flutter_studio/features/novels/models/novel_chapter_dto.dart';
import 'package:flutter_studio/features/novels/models/novel_character_dto.dart';
import 'package:flutter_studio/features/novels/models/novel_project_dto.dart';
import 'package:flutter_studio/features/novels/models/novel_world_entry_dto.dart';
import 'package:flutter_studio/features/novels/novel_api_client.dart';
import 'package:flutter_studio/features/novels/novel_controller.dart';
import 'package:flutter_studio/features/novels/novel_projects_page.dart';
import 'package:flutter_studio/features/novels/novel_state.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

Widget _wrap(Widget child) => MaterialApp(home: Scaffold(body: child));

class CreateProjectHttpClient extends http.BaseClient {
  String lastPostBody = '';

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    if (request is http.Request && request.method == 'POST') {
      lastPostBody = request.body;
      return _json({
        'id': 'p1',
        'title': 'Created Novel',
        'slug': 'created-novel',
        'status': 'active',
      });
    }
    return _json({'data': <Object?>[]});
  }

  http.StreamedResponse _json(Object body) {
    return http.StreamedResponse(
      Stream.value(utf8.encode(jsonEncode(body))),
      200,
      headers: {'content-type': 'application/json'},
    );
  }
}

void main() {
  testWidgets('capability controls Novel Studio navigation', (tester) async {
    await tester.pumpWidget(
      _wrap(
        buildShellNavigation(
          selectedIndex: 0,
          onSelected: (_) {},
          showNovelStudio: false,
        ),
      ),
    );
    expect(find.text('小说工作台'), findsNothing);

    await tester.pumpWidget(
      _wrap(
        buildShellNavigation(
          selectedIndex: novelStudioPageIndex,
          onSelected: (_) {},
          showNovelStudio: true,
        ),
      ),
    );
    expect(find.text('小说工作台', skipOffstage: false), findsOneWidget);
  });

  testWidgets('new project form submits to controller API', (tester) async {
    final httpClient = CreateProjectHttpClient();
    final controller = NovelController(
      NovelApiClient(
        LlmStudioClient('http://127.0.0.1:8000', httpClient: httpClient),
      ),
    );

    await tester.pumpWidget(_wrap(NovelProjectsPage(controller: controller)));
    await tester.enterText(find.byType(TextField).first, 'Created Novel');
    await tester.tap(find.text('创建项目'));
    await tester.pumpAndSettle();

    final body = jsonDecode(httpClient.lastPostBody) as Map;
    expect(body['title'], 'Created Novel');
  });

  testWidgets('project detail renders chapters characters and world entries', (
    tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(1400, 900));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    final controller = NovelController(
      NovelApiClient(LlmStudioClient('http://127.0.0.1:8000')),
    );
    controller.state = const NovelState(
      projects: [
        NovelProjectDto(
          id: 'p1',
          title: 'Novel',
          slug: 'novel',
          status: 'active',
        ),
      ],
      selectedProjectId: 'p1',
      chapters: [
        NovelChapterDto(
          id: 'c1',
          projectId: 'p1',
          title: 'Chapter 1',
          chapterIndex: 1,
          wordCount: 10,
          status: 'outline',
        ),
      ],
      characters: [
        NovelCharacterDto(
          id: 'ch1',
          projectId: 'p1',
          name: 'Alice',
          status: 'active',
          role: 'protagonist',
        ),
      ],
      worldEntries: [
        NovelWorldEntryDto(
          id: 'w1',
          projectId: 'p1',
          category: 'location',
          title: 'City',
          content: 'A city.',
          status: 'active',
        ),
      ],
    );

    await tester.pumpWidget(_wrap(NovelProjectsPage(controller: controller)));
    expect(find.text('Novel'), findsWidgets);

    await tester.tap(find.text('章节'));
    await tester.pumpAndSettle();
    expect(find.text('1. Chapter 1'), findsOneWidget);

    await tester.ensureVisible(find.text('人物'));
    await tester.tap(find.text('人物'), warnIfMissed: false);
    await tester.pumpAndSettle();
    expect(find.text('Alice'), findsOneWidget);

    await tester.ensureVisible(find.text('世界观设定'));
    await tester.tap(find.text('世界观设定'), warnIfMissed: false);
    await tester.pumpAndSettle();
    expect(find.text('City'), findsOneWidget);
  });
}
