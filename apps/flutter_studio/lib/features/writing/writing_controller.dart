import 'dart:async';

import 'package:flutter/foundation.dart';

import '../../core/api/api_exception.dart';
import '../memory/memory_api_client.dart';
import '../memory/models/memory_retrieval_result_dto.dart';
import '../revisions/models/revision_record_dto.dart';
import '../revisions/revision_api_client.dart';
import 'models/target_length_dto.dart';
import 'models/writing_generation_record_dto.dart';
import 'models/writing_generation_request_dto.dart';
import 'models/writing_stream_event_dto.dart';
import 'writing_api_client.dart';
import 'writing_state.dart';

class WritingController extends ChangeNotifier {
  WritingController(this._api, {this.revisionApi, this.memoryApi});

  final WritingApiClient _api;
  final RevisionApiClient? revisionApi;
  final MemoryApiClient? memoryApi;
  StreamSubscription<WritingStreamEventDto>? _streamSubscription;
  WritingState state = const WritingState();

  Future<void> refresh() async {
    await _run(() async {
      final projects = await _api.listProjects();
      final templates = await _api.listTemplates();
      final models = await _api.listModels();
      final adapters = await _api.listAdapters();
      final projectId = _existingOrFirst(
        state.selectedProjectId,
        projects.map((item) => item.id),
      );
      final templateId = _existingOrFirst(
        state.selectedTemplateId,
        templates.map((item) => item.id),
      );
      final modelId = _existingOrFirst(
        state.selectedModelId,
        models.map((item) => '${item['id'] ?? item['model_id'] ?? ''}'),
      );
      state = state.copyWith(
        projects: projects,
        templates: templates,
        models: models,
        adapters: adapters,
        selectedProjectId: projectId,
        selectedTemplateId: templateId,
        selectedModelId: modelId,
        clearProject: projectId == null,
        clearTemplate: templateId == null,
        clearModel: modelId == null,
      );
      if (projectId != null) {
        await _loadProject(projectId);
      }
    });
  }

  Future<void> selectProject(String? projectId) async {
    state = state.copyWith(
      selectedProjectId: projectId,
      clearProject: projectId == null,
      clearChapter: true,
      clearScene: true,
      clearPreview: true,
      history: const [],
      draftContent: '',
    );
    notifyListeners();
    if (projectId != null) {
      await _run(() => _loadProject(projectId));
    }
  }

  Future<void> selectChapter(String? chapterId) async {
    state = state.copyWith(
      selectedChapterId: chapterId,
      clearChapter: chapterId == null,
      clearScene: true,
      clearPreview: true,
      draftContent: _draftFor(chapterId),
    );
    notifyListeners();
    await _run(() async {
      state = state.copyWith(
        scenes: chapterId == null ? const [] : await _api.listScenes(chapterId),
        history: await _historyWithRevisionMap(
          projectId: state.selectedProjectId,
          chapterId: chapterId,
        ),
      );
    });
  }

  void selectScene(String? sceneId) {
    state = state.copyWith(
      selectedSceneId: sceneId,
      clearScene: sceneId == null,
      clearPreview: true,
    );
    notifyListeners();
  }

  void selectTemplate(String? templateId) {
    state = state.copyWith(
      selectedTemplateId: templateId,
      clearTemplate: templateId == null,
      clearPreview: true,
    );
    notifyListeners();
  }

  void selectModel(String? modelId) {
    state = state.copyWith(
      selectedModelId: modelId,
      clearModel: modelId == null,
    );
    notifyListeners();
  }

  void selectAdapter(String? adapterId) {
    state = state.copyWith(
      selectedAdapterId: adapterId,
      clearAdapter: adapterId == null || adapterId.isEmpty,
    );
    notifyListeners();
  }

  void selectMode(String mode) {
    state = state.copyWith(mode: mode);
    notifyListeners();
  }

  Future<void> renderContextPreview({
    required String currentChapterGoal,
    required TargetLengthDto targetLength,
    required int maxTokens,
  }) async {
    final projectId = state.selectedProjectId;
    final templateId = state.selectedTemplateId;
    if (projectId == null || templateId == null) {
      _setError('请先选择小说项目和 Prompt 模板。');
      return;
    }
    await _run(() async {
      final preview = await _api.renderContextPreview({
        'project_id': projectId,
        if (state.selectedChapterId != null)
          'chapter_id': state.selectedChapterId,
        if (state.selectedSceneId != null) 'scene_id': state.selectedSceneId,
        'template_id': templateId,
        'mode': state.mode,
        'target_budget': {
          'max_tokens': 32768,
          'reserved_output_tokens': maxTokens,
          'max_context_tokens': 12000,
          'max_chars': 48000,
          'hard_limit': true,
        },
        'user_variables': {
          if (currentChapterGoal.trim().isNotEmpty)
            'current_chapter_goal': currentChapterGoal.trim(),
          'target_length':
              '${targetLength.min}-${targetLength.max} ${targetLength.unit == 'chars' ? '中文字符' : 'tokens'}',
        },
        'memory': _memoryConfig(currentChapterGoal),
        'save_record': true,
      });
      state = state.copyWith(contextPreview: preview);
    });
  }

  Future<void> generate({
    required String currentChapterGoal,
    required TargetLengthDto targetLength,
    required double temperature,
    required double topP,
    required int maxTokens,
    required double repetitionPenalty,
    bool stream = true,
  }) async {
    final projectId = state.selectedProjectId;
    final templateId = state.selectedTemplateId;
    final modelId = state.selectedModelId;
    if (projectId == null || templateId == null || modelId == null) {
      _setError('请先选择小说项目、Prompt 模板和本地模型。');
      return;
    }
    final request = WritingGenerationRequestDto(
      projectId: projectId,
      chapterId: state.selectedChapterId,
      sceneId: state.selectedSceneId,
      templateId: templateId,
      modelId: modelId,
      adapterId: state.selectedAdapterId,
      mode: state.mode,
      targetLength: targetLength,
      userVariables: {
        if (currentChapterGoal.trim().isNotEmpty)
          'current_chapter_goal': currentChapterGoal.trim(),
      },
      memory: _memoryConfig(currentChapterGoal),
      temperature: temperature,
      topP: topP,
      maxTokens: maxTokens,
      repetitionPenalty: repetitionPenalty,
      stream: stream,
    );
    state = state.copyWith(
      generating: true,
      output: '',
      warnings: const [],
      clearGeneration: true,
      clearError: true,
      clearNotice: true,
    );
    notifyListeners();
    try {
      if (!stream) {
        final result = await _api.generateWriting(request);
        state = state.copyWith(
          generating: false,
          output: result.text,
          activeGenerationId: result.generationId,
          warnings: result.warnings,
          notice: '生成完成。',
        );
        notifyListeners();
        await _refreshHistory();
        return;
      }

      await _streamSubscription?.cancel();
      final completed = Completer<void>();
      _streamSubscription = _api
          .streamWriting(request)
          .listen(
            _handleStreamEvent,
            onError: (Object error) {
              _setError(_message(error), generating: false);
              if (!completed.isCompleted) {
                completed.complete();
              }
            },
            onDone: () {
              if (!completed.isCompleted) {
                completed.complete();
              }
            },
            cancelOnError: false,
          );
      await completed.future;
      state = state.copyWith(generating: false);
      notifyListeners();
      await _refreshHistory();
    } catch (error) {
      _setError(_message(error), generating: false);
    }
  }

  Future<void> stop() async {
    final generationId = state.activeGenerationId;
    if (generationId == null || !state.generating) {
      return;
    }
    try {
      await _api.cancelGeneration(generationId);
      state = state.copyWith(notice: '已请求停止生成。');
    } catch (error) {
      _setError(_message(error));
      return;
    }
    notifyListeners();
  }

  void setMemoryEnabled(bool value) {
    state = state.copyWith(
      memoryEnabled: value,
      clearMemoryPreview: !value,
      clearPreview: true,
    );
    notifyListeners();
  }

  void setMemoryTopK(int value) {
    final bounded = value < 1 ? 1 : (value > 50 ? 50 : value);
    state = state.copyWith(memoryTopK: bounded, clearPreview: true);
    notifyListeners();
  }

  void setMemoryMaxTokens(int value) {
    final bounded = value < 1 ? 1 : (value > 12000 ? 12000 : value);
    state = state.copyWith(memoryMaxTokens: bounded, clearPreview: true);
    notifyListeners();
  }

  void toggleMemorySourceType(String sourceType, bool selected) {
    final next = [...state.memorySourceTypes];
    if (selected && !next.contains(sourceType)) {
      next.add(sourceType);
    }
    if (!selected) {
      next.remove(sourceType);
    }
    state = state.copyWith(memorySourceTypes: next, clearPreview: true);
    notifyListeners();
  }

  Future<void> retrieveMemoryPreview(String queryText) async {
    final api = memoryApi;
    final projectId = state.selectedProjectId;
    if (api == null) {
    _setError('记忆系统不可用。');
      return;
    }
    if (projectId == null || projectId.isEmpty) {
      _setError('请先选择小说项目。');
      return;
    }
    await _run(() async {
      final result = await api.retrieveMemory(
        MemoryRetrieveRequest(
          projectId: projectId,
          chapterId: state.selectedChapterId,
          sceneId: state.selectedSceneId,
          queryText: queryText.trim().isEmpty ? ' ' : queryText.trim(),
          mode: state.mode,
          topK: state.memoryTopK,
          maxMemoryTokens: state.memoryMaxTokens,
          maxChunks: state.memoryTopK,
          sourceTypes: state.memorySourceTypes,
          saveRetrievalRecord: true,
        ),
      );
      state = state.copyWith(memoryPreview: result);
    });
  }

  Future<void> saveToChapter({bool append = false}) async {
    final generationId = state.activeGenerationId;
    if (generationId == null) {
      _setError('当前没有可保存的生成结果。');
      return;
    }
    state = state.copyWith(saving: true, clearError: true, clearNotice: true);
    notifyListeners();
    try {
      await _api.saveGenerationToChapter(
        generationId,
        target: 'draft_content',
        append: append,
      );
      final projectId = state.selectedProjectId;
      if (projectId != null) {
        final chapters = await _api.listChapters(projectId);
        state = state.copyWith(
          chapters: chapters,
          draftContent: _draftFrom(chapters, state.selectedChapterId),
        );
      }
      state = state.copyWith(
        saving: false,
        notice: append ? '已追加到章节草稿。' : '已保存到章节草稿。',
      );
    } catch (error) {
      state = state.copyWith(saving: false, error: _message(error));
    }
    notifyListeners();
  }

  Future<void> openGeneration(String generationId) async {
    await _run(() async {
      final record = await _api.getGeneration(generationId);
      state = state.copyWith(
        activeGenerationId: record.generationId,
        output: record.modelOutput,
        warnings: const [],
        notice: '已载入生成记录。',
      );
    });
  }

  Future<String?> createRevisionFromGeneration(
    String generationId, {
    String? editedText,
  }) async {
    final revisions = revisionApi;
    if (revisions == null) {
      _setError('修订系统当前不可用。');
      return null;
    }
    String? revisionId;
    await _run(() async {
      final revision = await revisions.createRevisionFromGeneration(
        generationId: generationId,
        editedText: editedText,
      );
      revisionId = revision.revisionId;
      await _refreshHistory();
      state = state.copyWith(notice: '修订已创建。');
    });
    return revisionId;
  }

  void _handleStreamEvent(WritingStreamEventDto event) {
    switch (event.type) {
      case 'start':
        state = state.copyWith(activeGenerationId: event.generationId);
      case 'delta':
        state = state.copyWith(output: '${state.output}${event.text ?? ''}');
      case 'done':
        state = state.copyWith(
          generating: false,
          activeGenerationId: event.generationId,
          warnings: event.warnings,
          notice: event.finishReason == 'cancelled'
              ? '生成已停止，部分输出已保存。'
              : '生成完成。',
        );
      case 'error':
        state = state.copyWith(
          generating: false,
          error:
              '${event.errorCode ?? 'WRITING_STREAM_FAILED'}: ${event.message ?? '流式生成失败。'}',
        );
    }
    notifyListeners();
  }

  Future<void> _loadProject(String projectId) async {
    final chapters = await _api.listChapters(projectId);
    final chapterId = _existingOrFirst(
      state.selectedChapterId,
      chapters.map((item) => item.id),
    );
    final scenes = chapterId == null
        ? const <dynamic>[]
        : await _api.listScenes(chapterId);
    final history = await _historyWithRevisionMap(
      projectId: projectId,
      chapterId: chapterId,
    );
    state = state.copyWith(
      chapters: chapters,
      scenes: scenes.cast(),
      selectedChapterId: chapterId,
      clearChapter: chapterId == null,
      clearScene: true,
      draftContent: _draftFrom(chapters, chapterId),
      history: history,
    );
  }

  Future<void> _refreshHistory() async {
    final projectId = state.selectedProjectId;
    if (projectId == null) {
      return;
    }
    try {
      final history = await _historyWithRevisionMap(
        projectId: projectId,
        chapterId: state.selectedChapterId,
      );
      state = state.copyWith(history: history);
      notifyListeners();
    } catch (error) {
      _setError(_message(error));
    }
  }

  Future<List<WritingGenerationRecordDto>> _historyWithRevisionMap({
    String? projectId,
    String? chapterId,
  }) async {
    final history = await _api.listGenerations(
      projectId: projectId,
      chapterId: chapterId,
    );
    final revisions = revisionApi == null || projectId == null
        ? const <RevisionRecordDto>[]
        : await revisionApi!.listRevisions(
            projectId: projectId,
            chapterId: chapterId,
          );
    state = state.copyWith(
      revisionIdsByGeneration: {
        for (final revision in revisions)
          if (revision.generationId != null)
            revision.generationId!: revision.revisionId,
      },
    );
    return history;
  }

  String _draftFor(String? chapterId) => _draftFrom(state.chapters, chapterId);

  static String _draftFrom(List<dynamic> chapters, String? chapterId) {
    for (final chapter in chapters) {
      if (chapter.id == chapterId) {
        return chapter.draftContent ?? '';
      }
    }
    return '';
  }

  static String? _existingOrFirst(String? selected, Iterable<String> values) {
    final items = values.where((value) => value.isNotEmpty).toList();
    if (selected != null && items.contains(selected)) {
      return selected;
    }
    return items.isEmpty ? null : items.first;
  }

  Map<String, Object?> _memoryConfig(String queryText) {
    if (!state.memoryEnabled) {
      return const {'enabled': false};
    }
    return {
      'enabled': true,
      'query_text': queryText.trim(),
      'top_k': state.memoryTopK,
      'max_memory_tokens': state.memoryMaxTokens,
      'max_chunks': state.memoryTopK,
      'source_types': state.memorySourceTypes,
      'save_retrieval_record': true,
    };
  }

  Future<void> _run(Future<void> Function() action) async {
    state = state.copyWith(loading: true, clearError: true, clearNotice: true);
    notifyListeners();
    try {
      await action();
      state = state.copyWith(loading: false);
    } catch (error) {
      state = state.copyWith(loading: false, error: _message(error));
    }
    notifyListeners();
  }

  void _setError(String message, {bool? generating}) {
    state = state.copyWith(error: message, generating: generating);
    notifyListeners();
  }

  static String _message(Object error) =>
      error is StudioApiException ? error.toString() : '$error';

  @override
  void dispose() {
    unawaited(_streamSubscription?.cancel());
    super.dispose();
  }
}
