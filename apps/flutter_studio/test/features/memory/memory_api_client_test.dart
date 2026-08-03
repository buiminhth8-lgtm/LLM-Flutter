import 'dart:convert';

import 'package:flutter_studio/core/api/api_client.dart';
import 'package:flutter_studio/features/memory/memory_api_client.dart';
import 'package:flutter_studio/features/memory/models/memory_build_request_dto.dart';
import 'package:flutter_studio/features/memory/models/memory_retrieval_result_dto.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

class MemoryContractHttpClient extends http.BaseClient {
  final List<http.BaseRequest> requests = [];

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    requests.add(request);
    final path = request.url.path;
    Object body = <String, Object?>{};
    if (path == '/v1/memory/documents' && request.method == 'GET') {
      body = {
        'data': [_document()],
      };
    } else if (path == '/v1/memory/documents' && request.method == 'POST') {
      body = _document();
    } else if (path.endsWith('/build-from-novel')) {
      body = {
        'project_id': 'p1',
        'documents_created': 1,
        'documents_updated': 0,
        'documents_unchanged': 0,
        'document_ids': ['doc-1'],
        'index': {'project_id': 'p1', 'chunks_indexed': 1},
      };
    } else if (path.endsWith('/index/rebuild')) {
      body = {'project_id': 'p1', 'chunks_indexed': 1};
    } else if (path.endsWith('/index/status')) {
      body = {
        'project_id': 'p1',
        'documents': {'total': 1, 'active': 1, 'stale': 0},
        'chunks': 1,
        'fts_available': true,
      };
    } else if (path == '/v1/memory/retrieve') {
      body = _retrieval();
    } else if (path == '/v1/memory/retrieval-records') {
      body = {
        'data': [
          {..._retrieval(), 'created_at': '2026-08-03T00:00:00Z'},
        ],
      };
    } else if (path.endsWith('/summaries') && request.method == 'GET') {
      body = {
        'data': [_summary()],
      };
    } else if (path.endsWith('/summaries') && request.method == 'POST') {
      body = _summary();
    } else if (path.endsWith('/summaries/generate')) {
      body = _summary(generatedBy: 'model');
    } else if (path.endsWith('/activate')) {
      body = _summary();
    } else if (request.method == 'PATCH' || request.method == 'DELETE') {
      body = _document(status: 'archived');
    }
    return http.StreamedResponse(
      Stream.value(utf8.encode(jsonEncode(body))),
      200,
      headers: {'content-type': 'application/json'},
    );
  }

  Map<String, Object?> _document({String status = 'active'}) => {
    'document_id': 'doc-1',
    'project_id': 'p1',
    'source_type': 'world_entry',
    'source_id': 'w1',
    'title': '黑市',
    'content': '黑市位于旧城地下。',
    'tags': ['地点'],
    'priority': 10,
    'status': status,
    'content_hash': 'hash',
    'metadata': {'category': '地点'},
    'created_at': '2026-08-03T00:00:00Z',
    'updated_at': '2026-08-03T00:00:00Z',
  };

  Map<String, Object?> _retrieval() => {
    'retrieval_id': 'ret-1',
    'project_id': 'p1',
    'query_text': '黑市',
    'mode': 'chapter_continue',
    'chunks': [
      {
        'chunk_id': 'chunk-1',
        'document_id': 'doc-1',
        'source_type': 'world_entry',
        'source_id': 'w1',
        'title': '黑市',
        'text': '黑市位于旧城地下。',
        'score': 0.92,
        'token_estimate': 12,
      },
    ],
    'retrieved_chunks': <Object?>[],
    'selected_chunks': ['chunk-1'],
    'total_token_estimate': 12,
    'warnings': <Object?>[],
  };

  Map<String, Object?> _summary({String generatedBy = 'manual'}) => {
    'summary_id': 'sum-1',
    'project_id': 'p1',
    'chapter_id': 'c1',
    'summary_type': 'short',
    'summary_text': '主角进入黑市。',
    'source_text_hash': 'hash',
    'generated_by': generatedBy,
    'status': 'active',
    'created_at': '2026-08-03T00:00:00Z',
  };
}

void main() {
  test(
    'Memory API client parses documents, retrieval, summaries and build',
    () async {
      final httpClient = MemoryContractHttpClient();
      final api = MemoryApiClient(
        LlmStudioClient('http://127.0.0.1:8000', httpClient: httpClient),
      );

      final docs = await api.listMemoryDocuments(projectId: 'p1');
      final created = await api.createMemoryDocument(
        const CreateMemoryDocumentRequest(
          projectId: 'p1',
          title: '黑市',
          content: '黑市位于旧城地下。',
        ),
      );
      final build = await api.buildMemoryFromNovel(
        'p1',
        const MemoryBuildRequest(),
      );
      final index = await api.rebuildProjectMemoryIndex('p1');
      final status = await api.memoryIndexStatus('p1');
      final retrieved = await api.retrieveMemory(
        const MemoryRetrieveRequest(projectId: 'p1', queryText: '黑市'),
      );
      final records = await api.listRetrievalRecords(projectId: 'p1');
      final summaries = await api.listChapterSummaries('c1');
      final summary = await api.createChapterSummary(
        'c1',
        const CreateChapterSummaryRequest(summaryText: '主角进入黑市。'),
      );
      final generated = await api.generateChapterSummary(
        'c1',
        const GenerateChapterSummaryRequest(modelId: 'm1'),
      );
      await api.activateChapterSummary('c1', summary.summaryId);
      await api.archiveMemoryDocument(created.documentId);

      expect(docs.single.title, '黑市');
      expect(build.documentsCreated, 1);
      expect(index.chunksIndexed, 1);
      expect(status['chunks'], 1);
      expect(retrieved.chunks.single.sourceType, 'world_entry');
      expect(records.single.retrievalId, 'ret-1');
      expect(summaries.single.summaryText, contains('黑市'));
      expect(generated.generatedBy, 'model');
    },
  );
}
