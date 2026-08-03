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
      final projects = _dedupeById(
        await _api.listProjects(),
        (project) => project.id,
      );
      final templates = _dedupeById(
        await _api.listTemplates(),
        (template) => template.id,
      );
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
      normalizeSelections();
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
      chapters: const [],
      scenes: const [],
    );
    normalizeSelections();
    notifyListeners();
    if (projectId != null && projectId.isNotEmpty) {
      await _run(() => _loadChapters(projectId));
    }
  }

  Future<void> selectChapter(String? chapterId) async {
    state = state.copyWith(
      selectedChapterId: chapterId,
      clearScene: true,
      clearResult: true,
      scenes: const [],
    );
    normalizeSelections();
    notifyListeners();
    if (chapterId != null && chapterId.isNotEmpty) {
      await _run(() async {
        final scenes = _dedupeById(
          await _api.listScenes(chapterId),
          (scene) => scene.id,
        );
        state = state.copyWith(scenes: scenes);
        normalizeSelections();
      });
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

  /// Validates all selected ids against the current lists and clears any
  /// stale selection, including selections that depend on a cleared parent.
  void normalizeSelections() {
    final projectIds = state.projects.map((project) => project.id).toSet();
    final chapterIds = state.chapters.map((chapter) => chapter.id).toSet();
    final sceneIds = state.scenes.map((scene) => scene.id).toSet();
    final templateIds = state.templates
        .map((template) => template.id)
        .toSet();

    final clearProject = !projectIds.contains(state.selectedProjectId);
    final keepChapter =
        !clearProject && chapterIds.contains(state.selectedChapterId);
    final keepScene = keepChapter && sceneIds.contains(state.selectedSceneId);
    final keepTemplate = templateIds.contains(state.selectedTemplateId);

    state = state.copyWith(
      clearProject: clearProject,
      selectedChapterId: keepChapter ? state.selectedChapterId : null,
      clearChapter: !keepChapter,
      selectedSceneId: keepScene ? state.selectedSceneId : null,
      clearScene: !keepScene,
      selectedTemplateId: keepTemplate ? state.selectedTemplateId : null,
      clearTemplate: !keepTemplate,
    );
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
    final chapters = _dedupeById(
      await _api.listChapters(projectId),
      (chapter) => chapter.id,
    );
    state = state.copyWith(
      chapters: chapters,
      scenes: const [],
      selectedChapterId: chapters.isEmpty ? null : chapters.first.id,
      clearChapter: chapters.isEmpty,
      clearScene: true,
    );
    if (chapters.isNotEmpty) {
      final scenes = _dedupeById(
        await _api.listScenes(chapters.first.id),
        (scene) => scene.id,
      );
      state = state.copyWith(scenes: scenes);
    }
    normalizeSelections();
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

List<T> _dedupeById<T>(List<T> items, String Function(T item) idOf) {
  final seen = <String>{};
  final result = <T>[];
  for (final item in items) {
    final id = idOf(item);
    if (id.isEmpty) {
      continue;
    }
    if (seen.add(id)) {
      result.add(item);
    }
  }
  return result;
}
