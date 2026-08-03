import 'dart:convert';

import 'package:http/http.dart' as http;

import '../errors/error_mapper.dart';
import '../logging/client_logger.dart';
import '../models/dto.dart';
import 'api_exception.dart';
import 'sse_client.dart';

class LlmStudioClient {
  LlmStudioClient(this.baseUrl, {http.Client? httpClient, this._sseClient})
    : _httpClient = httpClient ?? http.Client();

  String baseUrl;
  String userId = 'admin';
  String apiKey = '';
  final http.Client _httpClient;
  final SseClient? _sseClient;

  Future<Map<String, dynamic>> health() async =>
      _getMap('/health', authenticated: false);

  Future<Map<String, dynamic>> setupStatus() async =>
      _getMap('/v1/setup/status', authenticated: false);

  Future<Map<String, dynamic>> initialize({
    required String adminPassword,
  }) async {
    return _postMap(
      '/v1/setup/initialize',
      authenticated: false,
      body: {'admin_password': adminPassword, 'display_name': 'Admin'},
      timeout: const Duration(seconds: 15),
    );
  }

  Future<Map<String, dynamic>> runtime() async => _getMap('/v1/runtime');

  Future<List<dynamic>> capabilities() async {
    final body = await _getMap('/v1/capabilities');
    return (body['capabilities'] as List?) ?? const [];
  }

  Future<AuthUserDto> currentAuthUser() async {
    final body = await _getMap('/v1/auth/me');
    final user = body['user'];
    if (user is Map) {
      return AuthUserDto.fromMap(user);
    }
    throw StudioApiException('API response does not contain current user.');
  }

  Future<List<AuthUserDto>> authUsers() async {
    final body = await _getMap('/v1/auth/users');
    final users = (body['users'] as List?) ?? const [];
    return users
        .whereType<Map>()
        .map((item) => AuthUserDto.fromMap(item))
        .toList();
  }

  Future<RegeneratedApiKeyDto> regenerateApiKey(String userId) async {
    final body = await _postMap(
      '/v1/auth/users/${Uri.encodeComponent(userId)}/regenerate',
      body: const {},
    );
    return RegeneratedApiKeyDto.fromMap(body);
  }

  Future<List<dynamic>> models() async {
    final body = await _getMap('/v1/models');
    return (body['data'] as List?) ?? const [];
  }

  Future<void> scanModels() async {
    await _postMap('/v1/models/scan', timeout: const Duration(seconds: 15));
  }

  Future<Map<String, dynamic>> loadModel(String modelId) async {
    return _postMap(
      '/v1/models/${Uri.encodeComponent(modelId)}/load',
      body: {'strategy': 'auto'},
      timeout: const Duration(minutes: 10),
    );
  }

  Future<void> unloadModel(String modelId) async {
    await _postMap(
      '/v1/models/unload',
      body: {'model': modelId},
      timeout: const Duration(seconds: 30),
    );
  }

  Future<Map<String, dynamic>> currentModel() async =>
      _getMap('/v1/models/current');

  Future<Map<String, dynamic>> gpuScheduler() async =>
      _getMap('/v1/gpu/scheduler');

  Future<List<dynamic>> jobs({int limit = 20}) async {
    final body = await _getMap('/v1/jobs?limit=$limit');
    return (body['data'] as List?) ?? const [];
  }

  Future<List<DownloadTaskDto>> downloads() async {
    final body = await _getMap('/v1/downloads');
    final items = (body['data'] as List?) ?? const [];
    return items
        .whereType<Map>()
        .map((item) => DownloadTaskDto.fromMap(item))
        .toList();
  }

  Future<Map<String, dynamic>> startDownload({
    required String repoId,
    String provider = 'modelscope',
    String? revision,
    List<String>? allowPatterns,
    List<String>? ignorePatterns,
  }) {
    return _postMap(
      '/v1/downloads',
      body: {
        'provider': provider,
        'repo_id': repoId,
        if (revision != null && revision.isNotEmpty) 'revision': revision,
        if (allowPatterns != null && allowPatterns.isNotEmpty)
          'allow_patterns': allowPatterns,
        if (ignorePatterns != null && ignorePatterns.isNotEmpty)
          'ignore_patterns': ignorePatterns,
      },
    );
  }

  Future<void> cancelDownload(String id) async =>
      _postMap('/v1/downloads/${Uri.encodeComponent(id)}/cancel');

  Future<void> retryDownload(String id) async =>
      _postMap('/v1/downloads/${Uri.encodeComponent(id)}/retry');

  Future<void> deleteDownloadRecord(String id) async {
    final response = await _httpClient
        .delete(
          Uri.parse('$baseUrl/v1/downloads/${Uri.encodeComponent(id)}'),
          headers: _authHeaders(),
        )
        .timeout(const Duration(seconds: 30));
    _decodeMap(response);
  }

  Future<List<dynamic>> adapters() async {
    final body = await _getMap('/v1/adapters');
    return (body['data'] as List?) ?? (body['adapters'] as List?) ?? const [];
  }

  Future<void> scanAdapters() async => _postMap('/v1/adapters/scan');

  Future<void> loadAdapter(String id, String modelId) async => _postMap(
    '/v1/adapters/${Uri.encodeComponent(id)}/load',
    body: {'model': modelId},
  );

  Future<void> activateAdapter(String id, String modelId) async => _postMap(
    '/v1/adapters/${Uri.encodeComponent(id)}/activate',
    body: {'model': modelId},
  );

  Future<void> deactivateAdapter(String id, {String? modelId}) async =>
      _postMap(
        '/v1/adapters/${Uri.encodeComponent(id)}/deactivate',
        body: modelId == null || modelId.isEmpty
            ? const {}
            : {'model': modelId},
      );

  Future<void> unloadAdapter(String id, {String? modelId}) async => _postMap(
    '/v1/adapters/${Uri.encodeComponent(id)}/unload',
    body: modelId == null || modelId.isEmpty ? const {} : {'model': modelId},
  );

  Future<List<dynamic>> benchmarks() async {
    final body = await _getMap('/v1/benchmarks');
    return (body['data'] as List?) ?? const [];
  }

  Future<Map<String, dynamic>> startBenchmark({
    required String modelId,
    int maxNewTokens = 128,
    int contextLength = 512,
  }) {
    return _postMap(
      '/v1/benchmarks',
      body: {
        'model_id': modelId,
        'prompt_set': 'default',
        'warmup_runs': 1,
        'measured_runs': 3,
        'max_new_tokens': maxNewTokens,
        'context_lengths': [contextLength],
        'seed': 42,
      },
    );
  }

  Future<Map<String, dynamic>> storage() async => _getMap('/v1/storage');

  Future<Map<String, dynamic>> cleanupPreview() async =>
      _postMap('/v1/storage/cleanup/preview');

  Future<Map<String, dynamic>> cleanupStorage() async =>
      _postMap('/v1/storage/cleanup');

  Future<Map<String, dynamic>> exportDiagnostics() async =>
      _postMap('/v1/diagnostics/export');

  Future<List<dynamic>> novelProjects() async {
    final body = await _getMap('/v1/novels/projects');
    return (body['data'] as List?) ?? const [];
  }

  Future<Map<String, dynamic>> createNovelProject({
    required String title,
    String? genre,
    String? description,
    String? targetStyle,
    String? targetAudience,
  }) {
    return _postMap(
      '/v1/novels/projects',
      body: {
        'title': title,
        if (genre != null && genre.isNotEmpty) 'genre': genre,
        if (description != null && description.isNotEmpty)
          'description': description,
        if (targetStyle != null && targetStyle.isNotEmpty)
          'target_style': targetStyle,
        if (targetAudience != null && targetAudience.isNotEmpty)
          'target_audience': targetAudience,
      },
    );
  }

  Future<Map<String, dynamic>> updateNovelProject(
    String projectId,
    Map<String, Object?> body,
  ) => _patchMap('/v1/novels/projects/${Uri.encodeComponent(projectId)}', body);

  Future<void> deleteNovelProject(String projectId) async {
    await _deleteMap('/v1/novels/projects/${Uri.encodeComponent(projectId)}');
  }

  Future<List<dynamic>> novelVolumes(String projectId) async {
    final body = await _getMap(
      '/v1/novels/projects/${Uri.encodeComponent(projectId)}/volumes',
    );
    return (body['data'] as List?) ?? const [];
  }

  Future<Map<String, dynamic>> createNovelVolume(
    String projectId, {
    required String title,
    String? outline,
  }) => _postMap(
    '/v1/novels/projects/${Uri.encodeComponent(projectId)}/volumes',
    body: {
      'title': title,
      if (outline != null && outline.isNotEmpty) 'outline': outline,
    },
  );

  Future<List<dynamic>> novelChapters(String projectId) async {
    final body = await _getMap(
      '/v1/novels/projects/${Uri.encodeComponent(projectId)}/chapters',
    );
    return (body['data'] as List?) ?? const [];
  }

  Future<Map<String, dynamic>> createNovelChapter(
    String projectId, {
    required String title,
    String? outline,
    String? draftContent,
    String? summary,
  }) => _postMap(
    '/v1/novels/projects/${Uri.encodeComponent(projectId)}/chapters',
    body: {
      'title': title,
      if (outline != null && outline.isNotEmpty) 'outline': outline,
      if (draftContent != null && draftContent.isNotEmpty)
        'draft_content': draftContent,
      if (summary != null && summary.isNotEmpty) 'summary': summary,
    },
  );

  Future<Map<String, dynamic>> updateNovelChapter(
    String chapterId,
    Map<String, Object?> body,
  ) => _patchMap('/v1/novels/chapters/${Uri.encodeComponent(chapterId)}', body);

  Future<List<dynamic>> novelCharacters(String projectId) async {
    final body = await _getMap(
      '/v1/novels/projects/${Uri.encodeComponent(projectId)}/characters',
    );
    return (body['data'] as List?) ?? const [];
  }

  Future<Map<String, dynamic>> createNovelCharacter(
    String projectId, {
    required String name,
    String? role,
    String? notes,
  }) => _postMap(
    '/v1/novels/projects/${Uri.encodeComponent(projectId)}/characters',
    body: {
      'name': name,
      if (role != null && role.isNotEmpty) 'role': role,
      if (notes != null && notes.isNotEmpty) 'notes': notes,
    },
  );

  Future<List<dynamic>> novelWorldEntries(String projectId) async {
    final body = await _getMap(
      '/v1/novels/projects/${Uri.encodeComponent(projectId)}/world',
    );
    return (body['data'] as List?) ?? const [];
  }

  Future<Map<String, dynamic>> createNovelWorldEntry(
    String projectId, {
    required String category,
    required String title,
    required String content,
  }) => _postMap(
    '/v1/novels/projects/${Uri.encodeComponent(projectId)}/world',
    body: {'category': category, 'title': title, 'content': content},
  );

  Future<List<dynamic>> novelPlotThreads(String projectId) async {
    final body = await _getMap(
      '/v1/novels/projects/${Uri.encodeComponent(projectId)}/plot-threads',
    );
    return (body['data'] as List?) ?? const [];
  }

  Future<List<dynamic>> novelTimeline(String projectId) async {
    final body = await _getMap(
      '/v1/novels/projects/${Uri.encodeComponent(projectId)}/timeline',
    );
    return (body['data'] as List?) ?? const [];
  }

  Future<List<dynamic>> novelScenes(String chapterId) async {
    final body = await _getMap(
      '/v1/novels/chapters/${Uri.encodeComponent(chapterId)}/scenes',
    );
    return (body['data'] as List?) ?? const [];
  }

  Future<List<dynamic>> promptTemplates({
    String? type,
    String? scope,
    String? projectId,
  }) async {
    final query = <String, String>{
      if (type != null && type.isNotEmpty) 'type': type,
      if (scope != null && scope.isNotEmpty) 'scope': scope,
      if (projectId != null && projectId.isNotEmpty) 'project_id': projectId,
    };
    final path = Uri(
      path: '/v1/prompts/templates',
      queryParameters: query.isEmpty ? null : query,
    ).toString();
    final body = await _getMap(path);
    return (body['data'] as List?) ?? const [];
  }

  Future<Map<String, dynamic>> createPromptTemplate(Map<String, Object?> body) {
    return _postMap('/v1/prompts/templates', body: body);
  }

  Future<Map<String, dynamic>> updatePromptTemplate(
    String templateId,
    Map<String, Object?> body,
  ) {
    return _patchMap(
      '/v1/prompts/templates/${Uri.encodeComponent(templateId)}',
      body,
    );
  }

  Future<void> deletePromptTemplate(String templateId) async {
    await _deleteMap(
      '/v1/prompts/templates/${Uri.encodeComponent(templateId)}',
    );
  }

  Future<List<dynamic>> promptTemplateVersions(String templateId) async {
    final body = await _getMap(
      '/v1/prompts/templates/${Uri.encodeComponent(templateId)}/versions',
    );
    return (body['data'] as List?) ?? const [];
  }

  Future<Map<String, dynamic>> createPromptTemplateVersion(
    String templateId,
    Map<String, Object?> body,
  ) {
    return _postMap(
      '/v1/prompts/templates/${Uri.encodeComponent(templateId)}/versions',
      body: body,
    );
  }

  Future<Map<String, dynamic>> activatePromptTemplateVersion(
    String templateId,
    String versionId,
  ) {
    return _postMap(
      '/v1/prompts/templates/${Uri.encodeComponent(templateId)}/versions/${Uri.encodeComponent(versionId)}/activate',
      body: const {},
    );
  }

  Future<Map<String, dynamic>> renderPrompt(Map<String, Object?> body) {
    return _postMap('/v1/prompts/render', body: body);
  }

  Future<List<dynamic>> ensureDefaultPromptTemplates() async {
    final body = await _postMap('/v1/prompts/defaults/ensure', body: const {});
    return (body['data'] as List?) ?? const [];
  }

  Future<Map<String, dynamic>> copyPromptTemplateToProject(
    String templateId, {
    required String projectId,
    String? name,
  }) {
    return _postMap(
      '/v1/prompts/templates/${Uri.encodeComponent(templateId)}/copy-to-project',
      body: {
        'project_id': projectId,
        if (name != null && name.isNotEmpty) 'name': name,
      },
    );
  }

  Future<Map<String, dynamic>> assembleContext(Map<String, Object?> body) {
    return _postMap('/v1/context/assemble', body: body);
  }

  Future<Map<String, dynamic>> renderContextPreview(Map<String, Object?> body) {
    return _postMap('/v1/context/render-preview', body: body);
  }

  Future<Map<String, dynamic>> estimateContext(Map<String, Object?> body) {
    return _postMap('/v1/context/estimate', body: body);
  }

  Future<List<dynamic>> contextRecords({
    String? projectId,
    String? chapterId,
  }) async {
    final query = <String, String>{
      if (projectId != null && projectId.isNotEmpty) 'project_id': projectId,
      if (chapterId != null && chapterId.isNotEmpty) 'chapter_id': chapterId,
    };
    final path = Uri(
      path: '/v1/context/records',
      queryParameters: query.isEmpty ? null : query,
    ).toString();
    final body = await _getMap(path);
    return (body['data'] as List?) ?? const [];
  }

  Future<Map<String, dynamic>> writingGenerate(Map<String, Object?> body) {
    return _postMap(
      '/v1/writing/generate',
      body: body,
      timeout: const Duration(minutes: 10),
    );
  }

  Stream<Map<String, dynamic>> writingStream(Map<String, Object?> body) {
    final sse = _sseClient ?? SseClient();
    return sse.postJsonEvents(
      uri: Uri.parse('$baseUrl/v1/writing/stream'),
      headers: _authHeaders(),
      body: body,
    );
  }

  Future<Map<String, dynamic>> writingGeneration(String generationId) {
    return _getMap(
      '/v1/writing/generations/${Uri.encodeComponent(generationId)}',
    );
  }

  Future<List<dynamic>> writingGenerations({
    String? projectId,
    String? chapterId,
    String? mode,
    String? status,
    int limit = 50,
    int offset = 0,
  }) async {
    final query = <String, String>{
      if (projectId != null && projectId.isNotEmpty) 'project_id': projectId,
      if (chapterId != null && chapterId.isNotEmpty) 'chapter_id': chapterId,
      if (mode != null && mode.isNotEmpty) 'mode': mode,
      if (status != null && status.isNotEmpty) 'status': status,
      'limit': '$limit',
      'offset': '$offset',
    };
    final path = Uri(
      path: '/v1/writing/generations',
      queryParameters: query,
    ).toString();
    final body = await _getMap(path);
    return (body['data'] as List?) ?? const [];
  }

  Future<Map<String, dynamic>> saveWritingGeneration(
    String generationId, {
    String target = 'draft_content',
    bool append = false,
  }) {
    return _postMap(
      '/v1/writing/generations/${Uri.encodeComponent(generationId)}/save-to-chapter',
      body: {'target': target, 'append': append},
    );
  }

  Future<Map<String, dynamic>> cancelWritingGeneration(String generationId) {
    return _postMap(
      '/v1/writing/generations/${Uri.encodeComponent(generationId)}/cancel',
      body: const {},
    );
  }

  Future<List<dynamic>> revisions({
    String? projectId,
    String? chapterId,
    String? generationId,
    String? status,
    int? userScore,
    int limit = 50,
    int offset = 0,
  }) async {
    final query = <String, String>{
      if (projectId != null && projectId.isNotEmpty) 'project_id': projectId,
      if (chapterId != null && chapterId.isNotEmpty) 'chapter_id': chapterId,
      if (generationId != null && generationId.isNotEmpty)
        'generation_id': generationId,
      if (status != null && status.isNotEmpty) 'status': status,
      if (userScore != null) 'user_score': '$userScore',
      'limit': '$limit',
      'offset': '$offset',
    };
    final path = Uri(path: '/v1/revisions', queryParameters: query).toString();
    final body = await _getMap(path);
    return (body['data'] as List?) ?? const [];
  }

  Future<Map<String, dynamic>> revision(String revisionId) {
    return _getMap('/v1/revisions/${Uri.encodeComponent(revisionId)}');
  }

  Future<Map<String, dynamic>> updateRevision(
    String revisionId,
    Map<String, Object?> body,
  ) {
    return _patchMap('/v1/revisions/${Uri.encodeComponent(revisionId)}', body);
  }

  Future<Map<String, dynamic>> deleteRevision(String revisionId) {
    return _deleteMap('/v1/revisions/${Uri.encodeComponent(revisionId)}');
  }

  Future<Map<String, dynamic>> createRevisionFromGeneration(
    Map<String, Object?> body,
  ) {
    return _postMap('/v1/revisions/from-generation', body: body);
  }

  Future<Map<String, dynamic>> createRevisionFromChapterDraft(
    Map<String, Object?> body,
  ) {
    return _postMap('/v1/revisions/from-chapter-draft', body: body);
  }

  Future<Map<String, dynamic>> createManualRevision(Map<String, Object?> body) {
    return _postMap('/v1/revisions/manual', body: body);
  }

  Future<Map<String, dynamic>> approveRevision(String revisionId) {
    return _postMap(
      '/v1/revisions/${Uri.encodeComponent(revisionId)}/approve',
      body: const {},
    );
  }

  Future<Map<String, dynamic>> rejectRevision(
    String revisionId, {
    String? reason,
  }) {
    return _postMap(
      '/v1/revisions/${Uri.encodeComponent(revisionId)}/reject',
      body: {if (reason != null && reason.isNotEmpty) 'reason': reason},
    );
  }

  Future<Map<String, dynamic>> markRevisionDatasetCandidate(
    String revisionId,
    bool accepted,
  ) {
    return _postMap(
      '/v1/revisions/${Uri.encodeComponent(revisionId)}/dataset-candidate',
      body: {'accepted': accepted},
    );
  }

  Future<Map<String, dynamic>> autosaveRevision(Map<String, Object?> body) {
    return _postMap('/v1/revisions/autosave', body: body);
  }

  Future<List<dynamic>> revisionAutosaves(String revisionId) async {
    final body = await _getMap(
      '/v1/revisions/${Uri.encodeComponent(revisionId)}/autosaves',
    );
    return (body['data'] as List?) ?? const [];
  }

  Future<List<dynamic>> datasets({
    String? projectId,
    String? type,
    String? status,
    int limit = 50,
    int offset = 0,
  }) async {
    final query = <String, String>{
      if (projectId != null && projectId.isNotEmpty) 'project_id': projectId,
      if (type != null && type.isNotEmpty) 'type': type,
      if (status != null && status.isNotEmpty) 'status': status,
      'limit': '$limit',
      'offset': '$offset',
    };
    final path = Uri(path: '/v1/datasets', queryParameters: query).toString();
    final body = await _getMap(path);
    return (body['data'] as List?) ?? const [];
  }

  Future<Map<String, dynamic>> createDataset(Map<String, Object?> body) {
    return _postMap('/v1/datasets', body: body);
  }

  Future<Map<String, dynamic>> dataset(String datasetId) {
    return _getMap('/v1/datasets/${Uri.encodeComponent(datasetId)}');
  }

  Future<Map<String, dynamic>> updateDataset(
    String datasetId,
    Map<String, Object?> body,
  ) {
    return _patchMap('/v1/datasets/${Uri.encodeComponent(datasetId)}', body);
  }

  Future<Map<String, dynamic>> deleteDataset(String datasetId) {
    return _deleteMap('/v1/datasets/${Uri.encodeComponent(datasetId)}');
  }

  Future<Map<String, dynamic>> createDatasetSampleFromRevision(
    String datasetId,
    Map<String, Object?> body,
  ) {
    return _postMap(
      '/v1/datasets/${Uri.encodeComponent(datasetId)}/samples/from-revision',
      body: body,
    );
  }

  Future<Map<String, dynamic>> bulkCreateDatasetSamplesFromRevisions(
    String datasetId,
    Map<String, Object?> body,
  ) {
    return _postMap(
      '/v1/datasets/${Uri.encodeComponent(datasetId)}/samples/bulk-from-revisions',
      body: body,
    );
  }

  Future<List<dynamic>> datasetSamples(
    String datasetId, {
    String? status,
    String? sampleType,
    int limit = 50,
    int offset = 0,
  }) async {
    final query = <String, String>{
      if (status != null && status.isNotEmpty) 'status': status,
      if (sampleType != null && sampleType.isNotEmpty)
        'sample_type': sampleType,
      'limit': '$limit',
      'offset': '$offset',
    };
    final path = Uri(
      path: '/v1/datasets/${Uri.encodeComponent(datasetId)}/samples',
      queryParameters: query,
    ).toString();
    final body = await _getMap(path);
    return (body['data'] as List?) ?? const [];
  }

  Future<Map<String, dynamic>> datasetSample(String sampleId) {
    return _getMap('/v1/datasets/samples/${Uri.encodeComponent(sampleId)}');
  }

  Future<Map<String, dynamic>> updateDatasetSample(
    String sampleId,
    Map<String, Object?> body,
  ) {
    return _patchMap(
      '/v1/datasets/samples/${Uri.encodeComponent(sampleId)}',
      body,
    );
  }

  Future<Map<String, dynamic>> deleteDatasetSample(String sampleId) {
    return _deleteMap('/v1/datasets/samples/${Uri.encodeComponent(sampleId)}');
  }

  Future<Map<String, dynamic>> approveDatasetSample(String sampleId) {
    return _postMap(
      '/v1/datasets/samples/${Uri.encodeComponent(sampleId)}/approve',
      body: const {},
    );
  }

  Future<Map<String, dynamic>> rejectDatasetSample(
    String sampleId, {
    String? reason,
  }) {
    return _postMap(
      '/v1/datasets/samples/${Uri.encodeComponent(sampleId)}/reject',
      body: {if (reason != null && reason.isNotEmpty) 'reason': reason},
    );
  }

  Future<Map<String, dynamic>> exportDataset(
    String datasetId,
    Map<String, Object?> body,
  ) {
    return _postMap(
      '/v1/datasets/${Uri.encodeComponent(datasetId)}/export',
      body: body,
    );
  }

  Future<List<dynamic>> datasetExports(String datasetId) async {
    final body = await _getMap(
      '/v1/datasets/${Uri.encodeComponent(datasetId)}/exports',
    );
    return (body['data'] as List?) ?? const [];
  }

  Future<Map<String, dynamic>> datasetExport(String exportId) {
    return _getMap('/v1/datasets/exports/${Uri.encodeComponent(exportId)}');
  }

  Future<Map<String, dynamic>> markDatasetReady(String datasetId) {
    return _postMap(
      '/v1/datasets/${Uri.encodeComponent(datasetId)}/mark-ready',
      body: const {},
    );
  }

  Future<Map<String, dynamic>> markDatasetDirty(String datasetId) {
    return _postMap(
      '/v1/datasets/${Uri.encodeComponent(datasetId)}/mark-dirty',
      body: const {},
    );
  }

  Future<Map<String, dynamic>> freezeDatasetVersion(
    String datasetId,
    Map<String, Object?> body,
  ) {
    return _postMap(
      '/v1/datasets/${Uri.encodeComponent(datasetId)}/freeze',
      body: body,
      timeout: const Duration(minutes: 2),
    );
  }

  Future<List<dynamic>> datasetVersions(String datasetId) async {
    final body = await _getMap(
      '/v1/datasets/${Uri.encodeComponent(datasetId)}/versions',
    );
    return (body['data'] as List?) ?? const [];
  }

  Future<Map<String, dynamic>> datasetVersion(String datasetVersionId) {
    return _getMap(
      '/v1/datasets/versions/${Uri.encodeComponent(datasetVersionId)}',
    );
  }

  Future<Map<String, dynamic>> datasetVersionManifest(String datasetVersionId) {
    return _getMap(
      '/v1/datasets/versions/${Uri.encodeComponent(datasetVersionId)}/manifest',
    );
  }

  Future<List<dynamic>> datasetVersionSamples(
    String datasetVersionId, {
    String? split,
    bool? hasWarnings,
    int limit = 50,
    int offset = 0,
  }) async {
    final query = <String, String>{
      if (split != null && split.isNotEmpty) 'split': split,
      if (hasWarnings != null) 'has_warnings': '$hasWarnings',
      'limit': '$limit',
      'offset': '$offset',
    };
    final path = Uri(
      path:
          '/v1/datasets/versions/${Uri.encodeComponent(datasetVersionId)}/samples',
      queryParameters: query,
    ).toString();
    final body = await _getMap(path);
    return (body['data'] as List?) ?? const [];
  }

  Future<Map<String, dynamic>> recommendDatasetRecipe(
    String datasetVersionId,
    Map<String, Object?> body,
  ) {
    return _postMap(
      '/v1/datasets/versions/${Uri.encodeComponent(datasetVersionId)}/recommend-recipe',
      body: body,
    );
  }

  Future<List<dynamic>> datasetVersionRecipes(String datasetVersionId) async {
    final body = await _getMap(
      '/v1/datasets/versions/${Uri.encodeComponent(datasetVersionId)}/recipes',
    );
    return (body['data'] as List?) ?? const [];
  }

  Future<Map<String, dynamic>> datasetRecipe(String recipeId) {
    return _getMap('/v1/datasets/recipes/${Uri.encodeComponent(recipeId)}');
  }

  Future<Map<String, dynamic>> updateDatasetRecipe(
    String recipeId,
    Map<String, Object?> body,
  ) {
    return _patchMap(
      '/v1/datasets/recipes/${Uri.encodeComponent(recipeId)}',
      body,
    );
  }

  Future<Map<String, dynamic>> confirmDatasetRecipe(String recipeId) {
    return _postMap(
      '/v1/datasets/recipes/${Uri.encodeComponent(recipeId)}/confirm',
      body: const {},
    );
  }

  Future<Map<String, dynamic>> deleteDatasetRecipe(String recipeId) {
    return _deleteMap('/v1/datasets/recipes/${Uri.encodeComponent(recipeId)}');
  }

  Future<Map<String, dynamic>> preflightFinetune(
    Map<String, Object?> body,
  ) {
    return _postMap('/v1/finetune/preflight', body: body);
  }

  Future<Map<String, dynamic>> createFinetuneRun(
    Map<String, Object?> body,
  ) {
    return _postMap(
      '/v1/finetune/runs',
      body: body,
      timeout: const Duration(minutes: 2),
    );
  }

  Future<List<dynamic>> finetuneRuns({
    String? status,
    String? datasetVersionId,
    String? baseModelId,
    String? method,
    int limit = 50,
    int offset = 0,
  }) async {
    final query = <String, String>{
      if (status != null && status.isNotEmpty) 'status': status,
      if (datasetVersionId != null && datasetVersionId.isNotEmpty)
        'dataset_version_id': datasetVersionId,
      if (baseModelId != null && baseModelId.isNotEmpty)
        'base_model_id': baseModelId,
      if (method != null && method.isNotEmpty) 'method': method,
      'limit': '$limit',
      'offset': '$offset',
    };
    final body = await _getMap(
      Uri(path: '/v1/finetune/runs', queryParameters: query).toString(),
    );
    return (body['data'] as List?) ?? const [];
  }

  Future<Map<String, dynamic>> finetuneRun(String runId) {
    return _getMap('/v1/finetune/runs/${Uri.encodeComponent(runId)}');
  }

  Future<Map<String, dynamic>> startFinetuneRun(String runId) {
    return _postMap(
      '/v1/finetune/runs/${Uri.encodeComponent(runId)}/start',
      body: const {},
    );
  }

  Future<Map<String, dynamic>> cancelFinetuneRun(String runId) {
    return _postMap(
      '/v1/finetune/runs/${Uri.encodeComponent(runId)}/cancel',
      body: const {},
    );
  }

  Future<Map<String, dynamic>> resumeFinetuneRun(
    String runId, {
    String? checkpointId,
  }) {
    return _postMap(
      '/v1/finetune/runs/${Uri.encodeComponent(runId)}/resume',
      body: {
        if (checkpointId != null && checkpointId.isNotEmpty)
          'checkpoint_id': checkpointId,
      },
    );
  }

  Future<List<dynamic>> finetuneMetrics(String runId) async {
    final body = await _getMap(
      '/v1/finetune/runs/${Uri.encodeComponent(runId)}/metrics',
    );
    return (body['data'] as List?) ?? const [];
  }

  Future<List<dynamic>> finetuneLogs(String runId) async {
    final body = await _getMap(
      '/v1/finetune/runs/${Uri.encodeComponent(runId)}/logs',
    );
    return (body['data'] as List?) ?? const [];
  }

  Future<List<dynamic>> finetuneCheckpoints(String runId) async {
    final body = await _getMap(
      '/v1/finetune/runs/${Uri.encodeComponent(runId)}/checkpoints',
    );
    return (body['data'] as List?) ?? const [];
  }

  Future<String> ragQuery(String query, {int topK = 5}) async {
    final body = await _postMap(
      '/v1/rag/query',
      body: {'question': query, 'top_k': topK},
    );
    return jsonEncode(body);
  }

  Future<String> chat(
    String modelId,
    List<Map<String, String>> messages,
  ) async {
    final body = await _postMap(
      '/v1/chat/completions',
      body: {'model': modelId, 'messages': messages, 'stream': false},
      timeout: const Duration(minutes: 5),
    );
    final choices = body['choices'];
    if (choices is List && choices.isNotEmpty) {
      final message = choices.first['message'];
      if (message is Map && message['content'] is String) {
        return message['content'] as String;
      }
    }
    return jsonEncode(body);
  }

  Stream<String> chatStream(
    String modelId,
    List<Map<String, String>> messages,
  ) {
    final sse = _sseClient ?? SseClient();
    return sse.postJsonTokens(
      uri: Uri.parse('$baseUrl/v1/chat/completions'),
      headers: _authHeaders(),
      body: {'model': modelId, 'messages': messages, 'stream': true},
    );
  }

  Future<void> cancelJob(String id) async =>
      _postMap('/v1/jobs/${Uri.encodeComponent(id)}/cancel');

  Future<Map<String, dynamic>> registerExternalModel(String path) async {
    return _postMap('/v1/models/register', body: {'path': path});
  }

  Future<void> deleteModel(String modelId, {required bool confirm}) async {
    final uri = Uri.parse(
      '$baseUrl/v1/models/${Uri.encodeComponent(modelId)}',
    ).replace(queryParameters: {'confirm': confirm ? 'true' : 'false'});
    final response = await _httpClient
        .delete(uri, headers: _authHeaders())
        .timeout(const Duration(seconds: 30));
    _decodeMap(response);
  }

  Map<String, String> authHeadersForTesting() => _authHeaders();

  Future<Map<String, dynamic>> _getMap(
    String path, {
    bool authenticated = true,
  }) async {
    final response = await _httpClient
        .get(
          Uri.parse('$baseUrl$path'),
          headers: authenticated ? _authHeaders() : const {},
        )
        .timeout(const Duration(seconds: 8));
    return _decodeMap(response);
  }

  Future<Map<String, dynamic>> _postMap(
    String path, {
    Map<String, Object?>? body,
    bool authenticated = true,
    Duration timeout = const Duration(seconds: 30),
  }) async {
    final response = await _httpClient
        .post(
          Uri.parse('$baseUrl$path'),
          headers: {
            if (authenticated) ..._authHeaders(),
            'content-type': 'application/json',
          },
          body: body == null ? null : jsonEncode(body),
        )
        .timeout(timeout);
    return _decodeMap(response);
  }

  Future<Map<String, dynamic>> _patchMap(
    String path,
    Map<String, Object?> body,
  ) async {
    final response = await _httpClient
        .patch(
          Uri.parse('$baseUrl$path'),
          headers: {..._authHeaders(), 'content-type': 'application/json'},
          body: jsonEncode(body),
        )
        .timeout(const Duration(seconds: 30));
    return _decodeMap(response);
  }

  Future<Map<String, dynamic>> _deleteMap(String path) async {
    final response = await _httpClient
        .delete(Uri.parse('$baseUrl$path'), headers: _authHeaders())
        .timeout(const Duration(seconds: 30));
    return _decodeMap(response);
  }

  Map<String, dynamic> _decodeMap(http.Response response) {
    final dynamic body = response.body.isEmpty
        ? <String, dynamic>{}
        : jsonDecode(response.body);
    if (response.statusCode >= 400) {
      if (body is Map && body['error'] is Map) {
        final error = body['error'] as Map;
        final code = '${error['code']}';
        final message = '${error['message']}';
        logClientError('API ${response.statusCode} $code: $message');
        throw exceptionForApiError(
          statusCode: response.statusCode,
          code: code,
          message: message,
        );
      }
      logClientError('HTTP ${response.statusCode}: ${response.body}');
      throw StudioApiException(
        'HTTP ${response.statusCode}: ${response.body}',
        statusCode: response.statusCode,
      );
    }
    if (body is Map<String, dynamic>) {
      return body;
    }
    throw StudioApiException('API response is not a JSON object.');
  }

  Map<String, String> _authHeaders() {
    if (apiKey.isEmpty) {
      return const {};
    }
    final trimmedUserId = userId.trim();
    if (trimmedUserId.isEmpty) {
      return {'Authorization': 'Bearer $apiKey'};
    }
    return {
      'X-User-ID': trimmedUserId,
      'X-API-Key': apiKey,
      'Authorization': 'Bearer $apiKey',
    };
  }
}
