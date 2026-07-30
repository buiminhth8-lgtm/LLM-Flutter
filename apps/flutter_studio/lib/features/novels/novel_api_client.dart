import '../../core/api/api_client.dart';
import 'models/novel_chapter_dto.dart';
import 'models/novel_character_dto.dart';
import 'models/novel_plot_thread_dto.dart';
import 'models/novel_project_dto.dart';
import 'models/novel_timeline_event_dto.dart';
import 'models/novel_volume_dto.dart';
import 'models/novel_world_entry_dto.dart';

class NovelApiClient {
  NovelApiClient(this._client);

  final LlmStudioClient _client;

  Future<List<NovelProjectDto>> listProjects() async {
    final items = await _client.novelProjects();
    return items
        .whereType<Map>()
        .map((item) => NovelProjectDto.fromMap(item))
        .toList();
  }

  Future<NovelProjectDto> createProject({
    required String title,
    String? genre,
    String? description,
    String? targetStyle,
    String? targetAudience,
  }) async {
    final body = await _client.createNovelProject(
      title: title,
      genre: genre,
      description: description,
      targetStyle: targetStyle,
      targetAudience: targetAudience,
    );
    return NovelProjectDto.fromMap(body);
  }

  Future<void> deleteProject(String projectId) async {
    await _client.deleteNovelProject(projectId);
  }

  Future<List<NovelVolumeDto>> listVolumes(String projectId) async {
    final items = await _client.novelVolumes(projectId);
    return items
        .whereType<Map>()
        .map((item) => NovelVolumeDto.fromMap(item))
        .toList();
  }

  Future<NovelVolumeDto> createVolume(
    String projectId, {
    required String title,
    String? outline,
  }) async {
    final body = await _client.createNovelVolume(
      projectId,
      title: title,
      outline: outline,
    );
    return NovelVolumeDto.fromMap(body);
  }

  Future<List<NovelChapterDto>> listChapters(String projectId) async {
    final items = await _client.novelChapters(projectId);
    return items
        .whereType<Map>()
        .map((item) => NovelChapterDto.fromMap(item))
        .toList();
  }

  Future<NovelChapterDto> createChapter(
    String projectId, {
    required String title,
    String? outline,
    String? draftContent,
    String? summary,
  }) async {
    final body = await _client.createNovelChapter(
      projectId,
      title: title,
      outline: outline,
      draftContent: draftContent,
      summary: summary,
    );
    return NovelChapterDto.fromMap(body);
  }

  Future<List<NovelCharacterDto>> listCharacters(String projectId) async {
    final items = await _client.novelCharacters(projectId);
    return items
        .whereType<Map>()
        .map((item) => NovelCharacterDto.fromMap(item))
        .toList();
  }

  Future<NovelCharacterDto> createCharacter(
    String projectId, {
    required String name,
    String? role,
    String? notes,
  }) async {
    final body = await _client.createNovelCharacter(
      projectId,
      name: name,
      role: role,
      notes: notes,
    );
    return NovelCharacterDto.fromMap(body);
  }

  Future<List<NovelWorldEntryDto>> listWorldEntries(String projectId) async {
    final items = await _client.novelWorldEntries(projectId);
    return items
        .whereType<Map>()
        .map((item) => NovelWorldEntryDto.fromMap(item))
        .toList();
  }

  Future<NovelWorldEntryDto> createWorldEntry(
    String projectId, {
    required String category,
    required String title,
    required String content,
  }) async {
    final body = await _client.createNovelWorldEntry(
      projectId,
      category: category,
      title: title,
      content: content,
    );
    return NovelWorldEntryDto.fromMap(body);
  }

  Future<List<NovelPlotThreadDto>> listPlotThreads(String projectId) async {
    final items = await _client.novelPlotThreads(projectId);
    return items
        .whereType<Map>()
        .map((item) => NovelPlotThreadDto.fromMap(item))
        .toList();
  }

  Future<List<NovelTimelineEventDto>> listTimeline(String projectId) async {
    final items = await _client.novelTimeline(projectId);
    return items
        .whereType<Map>()
        .map((item) => NovelTimelineEventDto.fromMap(item))
        .toList();
  }
}
