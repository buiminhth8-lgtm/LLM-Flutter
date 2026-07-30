import 'models/novel_chapter_dto.dart';
import 'models/novel_character_dto.dart';
import 'models/novel_plot_thread_dto.dart';
import 'models/novel_project_dto.dart';
import 'models/novel_timeline_event_dto.dart';
import 'models/novel_volume_dto.dart';
import 'models/novel_world_entry_dto.dart';

class NovelState {
  const NovelState({
    this.projects = const [],
    this.volumes = const [],
    this.chapters = const [],
    this.characters = const [],
    this.worldEntries = const [],
    this.plotThreads = const [],
    this.timeline = const [],
    this.selectedProjectId,
    this.loading = false,
    this.error,
  });

  final List<NovelProjectDto> projects;
  final List<NovelVolumeDto> volumes;
  final List<NovelChapterDto> chapters;
  final List<NovelCharacterDto> characters;
  final List<NovelWorldEntryDto> worldEntries;
  final List<NovelPlotThreadDto> plotThreads;
  final List<NovelTimelineEventDto> timeline;
  final String? selectedProjectId;
  final bool loading;
  final String? error;

  NovelProjectDto? get selectedProject {
    for (final project in projects) {
      if (project.id == selectedProjectId) {
        return project;
      }
    }
    return projects.isEmpty ? null : projects.first;
  }

  NovelState copyWith({
    List<NovelProjectDto>? projects,
    List<NovelVolumeDto>? volumes,
    List<NovelChapterDto>? chapters,
    List<NovelCharacterDto>? characters,
    List<NovelWorldEntryDto>? worldEntries,
    List<NovelPlotThreadDto>? plotThreads,
    List<NovelTimelineEventDto>? timeline,
    String? selectedProjectId,
    bool clearSelectedProject = false,
    bool? loading,
    String? error,
    bool clearError = false,
  }) {
    return NovelState(
      projects: projects ?? this.projects,
      volumes: volumes ?? this.volumes,
      chapters: chapters ?? this.chapters,
      characters: characters ?? this.characters,
      worldEntries: worldEntries ?? this.worldEntries,
      plotThreads: plotThreads ?? this.plotThreads,
      timeline: timeline ?? this.timeline,
      selectedProjectId: clearSelectedProject
          ? null
          : selectedProjectId ?? this.selectedProjectId,
      loading: loading ?? this.loading,
      error: clearError ? null : error ?? this.error,
    );
  }
}
