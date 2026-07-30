import 'package:flutter/foundation.dart';

import '../../core/api/api_exception.dart';
import 'context_api_client.dart';
import 'context_state.dart';
import 'models/context_assembly_request_dto.dart';
import 'models/context_budget_dto.dart';

class ContextController extends ChangeNotifier {
  ContextController(this._api);

  final ContextApiClient _api;
  ContextState state = const ContextState();

  Future<void> refresh() async {
    await _run(() async {
      final projects = await _api.listProjects();
      final templates = await _api.listTemplates();
      state = state.copyWith(
        projects: projects,
        templates: templates,
        selectedProjectId:
            state.selectedProjectId ??
            (projects.isEmpty ? null : projects.first.id),
        selectedTemplateId:
            state.selectedTemplateId ??
            (templates.isEmpty ? null : templates.first.id),
      );
      if (state.selectedProjectId != null) {
        await _loadChapters(state.selectedProjectId!);
      }
    });
  }

  Future<void> selectProject(String? projectId) async {
    state = state.copyWith(
      selectedProjectId: projectId,
      clearChapter: true,
      clearScene: true,
      clearResult: true,
    );
    notifyListeners();
    if (projectId != null) {
      await _run(() => _loadChapters(projectId));
    }
  }

  Future<void> selectChapter(String? chapterId) async {
    state = state.copyWith(
      selectedChapterId: chapterId,
      clearScene: true,
      clearResult: true,
    );
    notifyListeners();
    if (chapterId != null) {
      await _run(() async {
        final scenes = await _api.listScenes(chapterId);
        state = state.copyWith(scenes: scenes);
      });
    } else {
      state = state.copyWith(scenes: const []);
      notifyListeners();
    }
  }

  void selectScene(String? sceneId) {
    state = state.copyWith(selectedSceneId: sceneId, clearResult: true);
    notifyListeners();
  }

  void selectTemplate(String? templateId) {
    state = templateId == null
        ? state.copyWith(clearTemplate: true, clearResult: true)
        : state.copyWith(selectedTemplateId: templateId, clearResult: true);
    notifyListeners();
  }

  Future<void> assemble({
    required ContextBudgetDto budget,
    required String currentChapterGoal,
    required String targetLength,
    bool renderPreview = false,
  }) async {
    final projectId = state.selectedProjectId;
    if (projectId == null) {
      state = state.copyWith(error: '请先选择小说项目。');
      notifyListeners();
      return;
    }
    await _run(() async {
      final request = ContextAssemblyRequestDto(
        projectId: projectId,
        chapterId: state.selectedChapterId,
        sceneId: state.selectedSceneId,
        templateId: renderPreview ? state.selectedTemplateId : null,
        targetBudget: budget,
        userVariables: {
          if (currentChapterGoal.trim().isNotEmpty)
            'current_chapter_goal': currentChapterGoal.trim(),
          if (targetLength.trim().isNotEmpty)
            'target_length': targetLength.trim(),
        },
      );
      if (renderPreview) {
        if (state.selectedTemplateId == null) {
          throw StateError('请先选择 Prompt 模板。');
        }
        final preview = await _api.renderContextPreview(request);
        state = state.copyWith(
          result: preview.assembly,
          preview: preview,
          clearError: true,
        );
      } else {
        final result = await _api.assembleContext(request);
        state = state.copyWith(
          result: result,
          clearPreview: true,
          clearError: true,
        );
      }
    });
  }

  Future<void> _loadChapters(String projectId) async {
    final chapters = await _api.listChapters(projectId);
    state = state.copyWith(
      chapters: chapters,
      scenes: const [],
      selectedChapterId: chapters.isEmpty ? null : chapters.first.id,
      clearChapter: chapters.isEmpty,
      clearScene: true,
    );
    if (chapters.isNotEmpty) {
      final scenes = await _api.listScenes(chapters.first.id);
      state = state.copyWith(scenes: scenes);
    }
  }

  Future<void> _run(Future<void> Function() action) async {
    state = state.copyWith(loading: true, clearError: true);
    notifyListeners();
    try {
      await action();
      state = state.copyWith(loading: false, clearError: true);
    } catch (error) {
      final message = error is StudioApiException ? error.message : '$error';
      state = state.copyWith(loading: false, error: message);
    }
    notifyListeners();
  }
}
