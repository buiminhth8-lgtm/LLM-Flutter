import 'dart:convert';

import 'package:flutter_studio/core/api/api_client.dart';
import 'package:flutter_studio/features/context_assembler/context_api_client.dart';
import 'package:flutter_studio/features/context_assembler/context_controller.dart';
import 'package:flutter_studio/features/novels/models/novel_chapter_dto.dart';
import 'package:flutter_studio/features/novels/models/novel_project_dto.dart';
import 'package:flutter_studio/features/prompt_studio/models/prompt_template_dto.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

class _FakeContextHttpClient extends http.BaseClient {
  _FakeContextHttpClient({
    this.projects = const [],
    this.templates = const [],
  });

  final List<Map<String, Object?>> projects;
  final List<Map<String, Object?>> templates;

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    final path = request.url.path;
    Object? data;
    if (path == '/v1/novels/projects') {
      data = projects;
    } else if (path == '/v1/prompts/templates') {
      data = templates;
    }
    return http.StreamedResponse(
      Stream.value(utf8.encode(jsonEncode({'data': data ?? <Object?>[]}))),
      200,
      headers: {'content-type': 'application/json'},
    );
  }
}

ContextController _controller(_FakeContextHttpClient client) {
  final controller = ContextController(
    ContextApiClient(
      LlmStudioClient('http://127.0.0.1:8000', httpClient: client),
    ),
  );
  return controller;
}

void main() {
  test('selectProject clears dependent chapter and scene selections', () async {
    final controller = _controller(_FakeContextHttpClient());
    addTearDown(controller.dispose);
    controller.state = controller.state.copyWith(
      projects: const [
        NovelProjectDto(id: 'p1', title: '项目一', slug: 'p1', status: 'active'),
      ],
      selectedProjectId: 'p-old',
      chapters: const [
        NovelChapterDto(
          id: 'c1',
          projectId: 'p-old',
          title: '旧章节',
          chapterIndex: 1,
          wordCount: 0,
          status: 'outline',
        ),
      ],
      selectedChapterId: 'c1',
      selectedSceneId: 's-old',
    );

    await controller.selectProject('p1');

    expect(controller.state.selectedProjectId, 'p1');
    expect(controller.state.selectedChapterId, isNull);
    expect(controller.state.selectedSceneId, isNull);
    expect(controller.state.chapters, isEmpty);
    expect(controller.state.scenes, isEmpty);
  });

  test('refresh clears stale selected project and template ids', () async {
    final controller = _controller(_FakeContextHttpClient());
    addTearDown(controller.dispose);
    controller.state = controller.state.copyWith(
      projects: const [
        NovelProjectDto(id: 'p1', title: '项目一', slug: 'p1', status: 'active'),
      ],
      selectedProjectId: 'p1',
      templates: const [
        PromptTemplateDto(
          id: 't1',
          name: '模板一',
          type: 'chapter_generate',
          scope: 'global',
          status: 'active',
        ),
      ],
      selectedTemplateId: 't1',
    );

    await controller.refresh();

    expect(controller.state.projects, isEmpty);
    expect(controller.state.templates, isEmpty);
    expect(controller.state.selectedProjectId, isNull);
    expect(controller.state.selectedTemplateId, isNull);
  });

  test('refresh dedupes duplicate projects and templates', () async {
    const p1 = {
      'id': 'p1',
      'title': '项目一',
      'slug': 'p1',
      'status': 'active',
    };
    const p2 = {
      'id': 'p2',
      'title': '项目二',
      'slug': 'p2',
      'status': 'active',
    };
    const t1 = {
      'id': 't1',
      'name': '模板一',
      'type': 'chapter_generate',
      'scope': 'global',
      'status': 'active',
    };
    final controller = _controller(
      _FakeContextHttpClient(
        projects: const [p1, p1, p2],
        templates: const [t1, t1],
      ),
    );
    addTearDown(controller.dispose);

    await controller.refresh();

    expect(controller.state.projects, hasLength(2));
    expect(controller.state.templates, hasLength(1));
    expect(controller.state.selectedProjectId, 'p1');
    expect(controller.state.selectedTemplateId, 't1');
  });

  test('refresh keeps valid selections after reload', () async {
    const p1 = {
      'id': 'p1',
      'title': '项目一',
      'slug': 'p1',
      'status': 'active',
    };
    const t1 = {
      'id': 't1',
      'name': '模板一',
      'type': 'chapter_generate',
      'scope': 'global',
      'status': 'active',
    };
    final controller = _controller(
      _FakeContextHttpClient(projects: const [p1], templates: const [t1]),
    );
    addTearDown(controller.dispose);
    controller.state = controller.state.copyWith(
      selectedProjectId: 'p1',
      selectedTemplateId: 't1',
    );

    await controller.refresh();

    expect(controller.state.selectedProjectId, 'p1');
    expect(controller.state.selectedTemplateId, 't1');
  });
}
