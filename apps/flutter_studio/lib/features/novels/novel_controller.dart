import 'package:flutter/foundation.dart';

import 'models/novel_chapter_dto.dart';
import 'models/novel_character_dto.dart';
import 'models/novel_plot_thread_dto.dart';
import 'models/novel_timeline_event_dto.dart';
import 'models/novel_volume_dto.dart';
import 'models/novel_world_entry_dto.dart';
import 'novel_api_client.dart';
import 'novel_state.dart';

class NovelController extends ChangeNotifier {
  NovelController(this._api);

  final NovelApiClient _api;
  NovelState state = const NovelState();

  Future<void> refresh() async {
    await _run(() async {
      final projects = await _api.listProjects();
      final selectedId =
          state.selectedProjectId ??
          (projects.isEmpty ? null : projects.first.id);
      state = state.copyWith(projects: projects, selectedProjectId: selectedId);
      if (selectedId == null) {
        state = state.copyWith(
          volumes: const [],
          chapters: const [],
          characters: const [],
          worldEntries: const [],
          plotThreads: const [],
          timeline: const [],
        );
        return;
      }
      await _refreshProjectDetails(selectedId);
    });
  }

  Future<void> selectProject(String projectId) async {
    state = state.copyWith(selectedProjectId: projectId);
    notifyListeners();
    await _run(() => _refreshProjectDetails(projectId));
  }

  Future<void> createProject({
    required String title,
    String? genre,
    String? description,
    String? targetStyle,
    String? targetAudience,
  }) async {
    await _run(() async {
      final project = await _api.createProject(
        title: title,
        genre: genre,
        description: description,
        targetStyle: targetStyle,
        targetAudience: targetAudience,
      );
      final projects = await _api.listProjects();
      state = state.copyWith(projects: projects, selectedProjectId: project.id);
      await _refreshProjectDetails(project.id);
    });
  }

  Future<void> deleteSelectedProject() async {
    final project = state.selectedProject;
    if (project == null) {
      return;
    }
    await _run(() async {
      await _api.deleteProject(project.id);
      final projects = await _api.listProjects();
      state = state.copyWith(
        projects: projects,
        selectedProjectId: projects.isEmpty ? null : projects.first.id,
      );
      if (projects.isNotEmpty) {
        await _refreshProjectDetails(projects.first.id);
      }
    });
  }

  Future<void> createChapter({
    required String title,
    String? outline,
    String? draftContent,
    String? summary,
  }) async {
    final project = state.selectedProject;
    if (project == null) {
      return;
    }
    await _run(() async {
      await _api.createChapter(
        project.id,
        title: title,
        outline: outline,
        draftContent: draftContent,
        summary: summary,
      );
      await _refreshProjectDetails(project.id);
    });
  }

  Future<void> createCharacter({
    required String name,
    String? role,
    String? notes,
  }) async {
    final project = state.selectedProject;
    if (project == null) {
      return;
    }
    await _run(() async {
      await _api.createCharacter(
        project.id,
        name: name,
        role: role,
        notes: notes,
      );
      await _refreshProjectDetails(project.id);
    });
  }

  Future<void> createWorldEntry({
    required String category,
    required String title,
    required String content,
  }) async {
    final project = state.selectedProject;
    if (project == null) {
      return;
    }
    await _run(() async {
      await _api.createWorldEntry(
        project.id,
        category: category,
        title: title,
        content: content,
      );
      await _refreshProjectDetails(project.id);
    });
  }

  Future<void> _refreshProjectDetails(String projectId) async {
    final results = await Future.wait<dynamic>([
      _api.listVolumes(projectId),
      _api.listChapters(projectId),
      _api.listCharacters(projectId),
      _api.listWorldEntries(projectId),
      _api.listPlotThreads(projectId),
      _api.listTimeline(projectId),
    ]);
    state = state.copyWith(
      volumes: results[0] as List<NovelVolumeDto>,
      chapters: results[1] as List<NovelChapterDto>,
      characters: results[2] as List<NovelCharacterDto>,
      worldEntries: results[3] as List<NovelWorldEntryDto>,
      plotThreads: results[4] as List<NovelPlotThreadDto>,
      timeline: results[5] as List<NovelTimelineEventDto>,
    );
  }

  Future<void> _run(Future<void> Function() action) async {
    state = state.copyWith(loading: true, clearError: true);
    notifyListeners();
    try {
      await action();
      state = state.copyWith(loading: false, clearError: true);
    } catch (error) {
      state = state.copyWith(loading: false, error: error.toString());
    }
    notifyListeners();
  }
}
