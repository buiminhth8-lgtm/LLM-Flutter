import 'dart:convert';

import 'package:flutter_studio/core/api/api_client.dart';
import 'package:flutter_studio/features/revisions/models/revision_autosave_dto.dart';
import 'package:flutter_studio/features/revisions/models/revision_record_dto.dart';
import 'package:flutter_studio/features/revisions/revision_api_client.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

class RevisionApiHttpClient extends http.BaseClient {
  final List<String> paths = [];
  bool updated = false;

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    paths.add('${request.method} ${request.url.path}');
    final path = request.url.path;
    Object response = _record();
    if (path == '/v1/revisions') {
      response = {
        'data': [_record()],
      };
    } else if (request.method == 'PATCH') {
      updated = true;
      response = _record(editedText: 'saved text');
    } else if (path == '/v1/revisions/autosave') {
      response = {
        'autosave_id': 'auto-1',
        'revision_id': 'rev-1',
        'project_id': 'p1',
        'draft_text': 'draft',
        'draft_hash': 'hash',
        'client_revision': 2,
        'created_at': '2026-07-31T00:00:00Z',
      };
    } else if (path.endsWith('/autosaves')) {
      response = {
        'data': [
          {
            'autosave_id': 'auto-1',
            'revision_id': 'rev-1',
            'project_id': 'p1',
            'draft_text': 'draft',
            'draft_hash': 'hash',
            'client_revision': 2,
            'created_at': '2026-07-31T00:00:00Z',
          },
        ],
      };
    }
    return http.StreamedResponse(
      Stream.value(utf8.encode(jsonEncode(response))),
      200,
      headers: {'content-type': 'application/json'},
    );
  }

  Map<String, Object?> _record({String editedText = 'edited'}) => {
    'revision_id': 'rev-1',
    'generation_id': 'gen-1',
    'project_id': 'p1',
    'chapter_id': 'c1',
    'original_text': 'original',
    'edited_text': editedText,
    'diff': {
      'summary': {
        'original_chars': 8,
        'edited_chars': 6,
        'added_chars': 2,
        'removed_chars': 4,
        'changed_blocks': 1,
      },
      'ops': [
        {'type': 'delete', 'text': 'old'},
        {'type': 'insert', 'text': 'new'},
      ],
    },
    'edit_tags': ['language_polish'],
    'user_score': 4,
    'status': 'draft',
    'accepted_for_dataset': true,
    'source': 'generation',
    'original_hash': 'oh',
    'edited_hash': 'eh',
    'created_at': '2026-07-31T00:00:00Z',
    'updated_at': '2026-07-31T00:00:00Z',
  };
}

void main() {
  test('Revision DTO parses record and diff_json', () {
    final dto = RevisionRecordDto.fromMap({
      'id': 'rev-1',
      'project_id': 'p1',
      'original_text': 'old',
      'edited_text': 'new',
      'diff_json': {
        'summary': {'changed_blocks': 1},
        'ops': [
          {'type': 'insert', 'text': 'new'},
        ],
      },
      'edit_tags': ['detail_expand'],
      'status': 'approved',
      'accepted_for_dataset': 1,
      'source': 'manual',
      'original_hash': 'a',
      'edited_hash': 'b',
      'created_at': 'now',
      'updated_at': 'now',
    });

    expect(dto.revisionId, 'rev-1');
    expect(dto.diff.ops.single.type, 'insert');
    expect(dto.acceptedForDataset, isTrue);
  });

  test('Revision API client calls create, update, list and autosave', () async {
    final httpClient = RevisionApiHttpClient();
    final api = RevisionApiClient(
      LlmStudioClient('http://127.0.0.1:8000', httpClient: httpClient),
    );

    final created = await api.createRevisionFromGeneration(
      generationId: 'gen-1',
    );
    final listed = await api.listRevisions(projectId: 'p1');
    final updated = await api.updateRevision(
      'rev-1',
      const RevisionUpdateRequest(editedText: 'saved text'),
    );
    final autosave = await api.autosaveRevision(
      const RevisionAutosaveRequest(
        revisionId: 'rev-1',
        projectId: 'p1',
        draftText: 'draft',
        clientRevision: 2,
      ),
    );

    expect(created.originalText, 'original');
    expect(listed.single.revisionId, 'rev-1');
    expect(updated.editedText, 'saved text');
    expect(autosave.clientRevision, 2);
    expect(httpClient.updated, isTrue);
  });
}
