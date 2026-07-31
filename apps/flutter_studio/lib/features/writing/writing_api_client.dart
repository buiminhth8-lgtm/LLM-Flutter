import '../../core/api/api_client.dart';
import '../context_assembler/models/context_render_preview_dto.dart';
import '../novels/models/novel_chapter_dto.dart';
import '../novels/models/novel_project_dto.dart';
import '../novels/models/novel_scene_dto.dart';
import '../prompt_studio/models/prompt_template_dto.dart';
import 'models/writing_generation_record_dto.dart';
import 'models/writing_generation_request_dto.dart';
import 'models/writing_generation_result_dto.dart';
import 'models/writing_stream_event_dto.dart';

class WritingApiClient {
  WritingApiClient(this._client);

  final LlmStudioClient _client;

  Future<WritingGenerationResultDto> generateWriting(
    WritingGenerationRequestDto request,
  ) async {
    final body = await _client.writingGenerate(request.toMap());
    return WritingGenerationResultDto.fromMap(body);
  }

  Stream<WritingStreamEventDto> streamWriting(
    WritingGenerationRequestDto request,
  ) {
    return _client
        .writingStream(request.toMap())
        .map(WritingStreamEventDto.fromMap);
  }

  Future<WritingGenerationRecordDto> getGeneration(String generationId) async {
    final body = await _client.writingGeneration(generationId);
    return WritingGenerationRecordDto.fromMap(body);
  }

  Future<List<WritingGenerationRecordDto>> listGenerations({
    String? projectId,
    String? chapterId,
    String? mode,
    String? status,
  }) async {
    final items = await _client.writingGenerations(
      projectId: projectId,
      chapterId: chapterId,
      mode: mode,
      status: status,
    );
    return items
        .whereType<Map>()
        .map(WritingGenerationRecordDto.fromMap)
        .toList(growable: false);
  }

  Future<void> saveGenerationToChapter(
    String generationId, {
    String target = 'draft_content',
    bool append = false,
  }) async {
    await _client.saveWritingGeneration(
      generationId,
      target: target,
      append: append,
    );
  }

  Future<void> cancelGeneration(String generationId) async {
    await _client.cancelWritingGeneration(generationId);
  }

  Future<List<NovelProjectDto>> listProjects() async {
    final items = await _client.novelProjects();
    return items
        .whereType<Map>()
        .map(NovelProjectDto.fromMap)
        .toList(growable: false);
  }

  Future<List<NovelChapterDto>> listChapters(String projectId) async {
    final items = await _client.novelChapters(projectId);
    return items
        .whereType<Map>()
        .map(NovelChapterDto.fromMap)
        .toList(growable: false);
  }

  Future<List<NovelSceneDto>> listScenes(String chapterId) async {
    final items = await _client.novelScenes(chapterId);
    return items
        .whereType<Map>()
        .map(NovelSceneDto.fromMap)
        .toList(growable: false);
  }

  Future<List<PromptTemplateDto>> listTemplates() async {
    final items = await _client.promptTemplates();
    return items
        .whereType<Map>()
        .map(PromptTemplateDto.fromMap)
        .toList(growable: false);
  }

  Future<List<Map<String, dynamic>>> listModels() async {
    final items = await _client.models();
    return items
        .whereType<Map>()
        .map((item) => item.map((key, value) => MapEntry('$key', value)))
        .toList(growable: false);
  }

  Future<List<Map<String, dynamic>>> listAdapters() async {
    final items = await _client.adapters();
    return items
        .whereType<Map>()
        .map((item) => item.map((key, value) => MapEntry('$key', value)))
        .toList(growable: false);
  }

  Future<ContextRenderPreviewDto> renderContextPreview(
    Map<String, Object?> request,
  ) async {
    final body = await _client.renderContextPreview(request);
    return ContextRenderPreviewDto.fromMap(body);
  }
}
