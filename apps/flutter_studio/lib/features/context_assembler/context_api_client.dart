import '../../core/api/api_client.dart';
import '../novels/models/novel_chapter_dto.dart';
import '../novels/models/novel_project_dto.dart';
import '../novels/models/novel_scene_dto.dart';
import '../prompt_studio/models/prompt_template_dto.dart';
import 'models/context_assembly_request_dto.dart';
import 'models/context_assembly_result_dto.dart';
import 'models/context_render_preview_dto.dart';

class ContextApiClient {
  ContextApiClient(this._client);

  final LlmStudioClient _client;

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

  Future<ContextAssemblyResultDto> assembleContext(
    ContextAssemblyRequestDto request,
  ) async {
    final body = await _client.assembleContext(request.toMap());
    return ContextAssemblyResultDto.fromMap(body);
  }

  Future<ContextRenderPreviewDto> renderContextPreview(
    ContextAssemblyRequestDto request,
  ) async {
    final body = await _client.renderContextPreview(request.toMap());
    return ContextRenderPreviewDto.fromMap(body);
  }

  Future<({int estimatedTokens, int estimatedChars})> estimateContext(
    String text,
  ) async {
    final body = await _client.estimateContext({'text': text});
    return (
      estimatedTokens: (body['estimated_tokens'] as num?)?.toInt() ?? 0,
      estimatedChars: (body['estimated_chars'] as num?)?.toInt() ?? 0,
    );
  }

  Future<List<ContextAssemblyResultDto>> listContextRecords({
    String? projectId,
    String? chapterId,
  }) async {
    final items = await _client.contextRecords(
      projectId: projectId,
      chapterId: chapterId,
    );
    return items
        .whereType<Map>()
        .map(ContextAssemblyResultDto.fromMap)
        .toList(growable: false);
  }
}
