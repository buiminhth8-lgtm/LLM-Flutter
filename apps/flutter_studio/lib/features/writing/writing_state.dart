import '../context_assembler/models/context_render_preview_dto.dart';
import '../novels/models/novel_chapter_dto.dart';
import '../novels/models/novel_project_dto.dart';
import '../novels/models/novel_scene_dto.dart';
import '../prompt_studio/models/prompt_template_dto.dart';
import 'models/writing_generation_record_dto.dart';

class WritingState {
  const WritingState({
    this.projects = const [],
    this.chapters = const [],
    this.scenes = const [],
    this.templates = const [],
    this.models = const [],
    this.adapters = const [],
    this.history = const [],
    this.selectedProjectId,
    this.selectedChapterId,
    this.selectedSceneId,
    this.selectedTemplateId,
    this.selectedModelId,
    this.selectedAdapterId,
    this.mode = 'chapter_generate',
    this.draftContent = '',
    this.output = '',
    this.activeGenerationId,
    this.contextPreview,
    this.warnings = const [],
    this.loading = false,
    this.generating = false,
    this.saving = false,
    this.error,
    this.notice,
  });

  final List<NovelProjectDto> projects;
  final List<NovelChapterDto> chapters;
  final List<NovelSceneDto> scenes;
  final List<PromptTemplateDto> templates;
  final List<Map<String, dynamic>> models;
  final List<Map<String, dynamic>> adapters;
  final List<WritingGenerationRecordDto> history;
  final String? selectedProjectId;
  final String? selectedChapterId;
  final String? selectedSceneId;
  final String? selectedTemplateId;
  final String? selectedModelId;
  final String? selectedAdapterId;
  final String mode;
  final String draftContent;
  final String output;
  final String? activeGenerationId;
  final ContextRenderPreviewDto? contextPreview;
  final List<Map<String, dynamic>> warnings;
  final bool loading;
  final bool generating;
  final bool saving;
  final String? error;
  final String? notice;

  WritingState copyWith({
    List<NovelProjectDto>? projects,
    List<NovelChapterDto>? chapters,
    List<NovelSceneDto>? scenes,
    List<PromptTemplateDto>? templates,
    List<Map<String, dynamic>>? models,
    List<Map<String, dynamic>>? adapters,
    List<WritingGenerationRecordDto>? history,
    String? selectedProjectId,
    String? selectedChapterId,
    String? selectedSceneId,
    String? selectedTemplateId,
    String? selectedModelId,
    String? selectedAdapterId,
    String? mode,
    String? draftContent,
    String? output,
    String? activeGenerationId,
    ContextRenderPreviewDto? contextPreview,
    List<Map<String, dynamic>>? warnings,
    bool? loading,
    bool? generating,
    bool? saving,
    String? error,
    String? notice,
    bool clearProject = false,
    bool clearChapter = false,
    bool clearScene = false,
    bool clearTemplate = false,
    bool clearModel = false,
    bool clearAdapter = false,
    bool clearGeneration = false,
    bool clearPreview = false,
    bool clearError = false,
    bool clearNotice = false,
  }) => WritingState(
    projects: projects ?? this.projects,
    chapters: chapters ?? this.chapters,
    scenes: scenes ?? this.scenes,
    templates: templates ?? this.templates,
    models: models ?? this.models,
    adapters: adapters ?? this.adapters,
    history: history ?? this.history,
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
    selectedModelId: clearModel
        ? null
        : selectedModelId ?? this.selectedModelId,
    selectedAdapterId: clearAdapter
        ? null
        : selectedAdapterId ?? this.selectedAdapterId,
    mode: mode ?? this.mode,
    draftContent: draftContent ?? this.draftContent,
    output: output ?? this.output,
    activeGenerationId: clearGeneration
        ? null
        : activeGenerationId ?? this.activeGenerationId,
    contextPreview: clearPreview ? null : contextPreview ?? this.contextPreview,
    warnings: warnings ?? this.warnings,
    loading: loading ?? this.loading,
    generating: generating ?? this.generating,
    saving: saving ?? this.saving,
    error: clearError ? null : error ?? this.error,
    notice: clearNotice ? null : notice ?? this.notice,
  );
}
