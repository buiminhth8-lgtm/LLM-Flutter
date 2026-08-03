import '../novels/models/novel_chapter_dto.dart';
import '../novels/models/novel_project_dto.dart';
import '../novels/models/novel_scene_dto.dart';
import '../prompt_studio/models/prompt_template_dto.dart';
import 'models/context_assembly_result_dto.dart';
import 'models/context_render_preview_dto.dart';

class ContextState {
  const ContextState({
    this.projects = const [],
    this.chapters = const [],
    this.scenes = const [],
    this.templates = const [],
    this.selectedProjectId,
    this.selectedChapterId,
    this.selectedSceneId,
    this.selectedTemplateId,
    this.result,
    this.preview,
    this.loading = false,
    this.error,
  });

  final List<NovelProjectDto> projects;
  final List<NovelChapterDto> chapters;
  final List<NovelSceneDto> scenes;
  final List<PromptTemplateDto> templates;
  final String? selectedProjectId;
  final String? selectedChapterId;
  final String? selectedSceneId;
  final String? selectedTemplateId;
  final ContextAssemblyResultDto? result;
  final ContextRenderPreviewDto? preview;
  final bool loading;
  final String? error;

  ContextState copyWith({
    List<NovelProjectDto>? projects,
    List<NovelChapterDto>? chapters,
    List<NovelSceneDto>? scenes,
    List<PromptTemplateDto>? templates,
    String? selectedProjectId,
    String? selectedChapterId,
    String? selectedSceneId,
    String? selectedTemplateId,
    ContextAssemblyResultDto? result,
    ContextRenderPreviewDto? preview,
    bool? loading,
    String? error,
    bool clearProject = false,
    bool clearChapter = false,
    bool clearScene = false,
    bool clearTemplate = false,
    bool clearResult = false,
    bool clearPreview = false,
    bool clearError = false,
  }) => ContextState(
    projects: projects ?? this.projects,
    chapters: chapters ?? this.chapters,
    scenes: scenes ?? this.scenes,
    templates: templates ?? this.templates,
    selectedProjectId: clearProject
        ? null
        : selectedProjectId ?? this.selectedProjectId,
    selectedChapterId: clearChapter
        ? null
        : selectedChapterId ?? this.selectedChapterId,
    selectedSceneId: clearScene
        ? null
        : selectedSceneId ?? this.selectedSceneId,
    selectedTemplateId: clearTemplate
        ? null
        : selectedTemplateId ?? this.selectedTemplateId,
    result: clearResult ? null : result ?? this.result,
    preview: clearResult || clearPreview ? null : preview ?? this.preview,
    loading: loading ?? this.loading,
    error: clearError ? null : error ?? this.error,
  );
}
