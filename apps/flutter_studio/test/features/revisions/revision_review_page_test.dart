import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_studio/app/app_routes.dart';
import 'package:flutter_studio/core/api/api_client.dart';
import 'package:flutter_studio/features/revisions/revision_api_client.dart';
import 'package:flutter_studio/features/revisions/revision_controller.dart';
import 'package:flutter_studio/features/revisions/revision_review_page.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

class RevisionReviewHttpClient extends http.BaseClient {
  bool saved = false;
  bool candidateMarked = false;

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    final path = request.url.path;
    Object response = _record();
    if (path == '/v1/revisions') {
      response = {
        'data': [_record()],
      };
    } else if (request.method == 'PATCH') {
      saved = true;
      response = _record(editedText: 'edited by tester');
    } else if (path.endsWith('/dataset-candidate')) {
      candidateMarked = true;
      response = _record(accepted: true);
    } else if (path == '/v1/revisions/autosave') {
      response = {
        'autosave_id': 'auto-1',
        'revision_id': 'rev-1',
        'project_id': 'p1',
        'draft_text': 'edited by tester',
        'draft_hash': 'hash',
        'client_revision': 1,
        'created_at': '2026-07-31T00:00:00Z',
      };
    }
    return http.StreamedResponse(
      Stream.value(utf8.encode(jsonEncode(response))),
      200,
      headers: {'content-type': 'application/json'},
    );
  }

  Map<String, Object?> _record({
    String editedText = 'edited',
    bool accepted = false,
  }) => {
    'revision_id': 'rev-1',
    'generation_id': 'gen-1',
    'project_id': 'p1',
    'chapter_id': 'c1',
    'original_text': 'model original',
    'edited_text': editedText,
    'diff': {
      'summary': {
        'original_chars': 14,
        'edited_chars': editedText.length,
        'added_chars': 3,
        'removed_chars': 2,
        'changed_blocks': 1,
      },
      'ops': [
        {'type': 'delete', 'text': 'model'},
        {'type': 'insert', 'text': 'human'},
      ],
    },
    'edit_tags': ['language_polish'],
    'user_score': 4,
    'quality_notes': 'notes',
    'status': 'draft',
    'accepted_for_dataset': accepted,
    'source': 'generation',
    'original_hash': 'oh',
    'edited_hash': 'eh',
    'created_at': '2026-07-31T00:00:00Z',
    'updated_at': '2026-07-31T00:00:00Z',
  };
}

void main() {
  testWidgets('Revision Review page displays original, edits and saves', (
    tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(1500, 1000));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    final httpClient = RevisionReviewHttpClient();
    final controller = RevisionController(
      RevisionApiClient(
        LlmStudioClient('http://127.0.0.1:8000', httpClient: httpClient),
      ),
    );
    addTearDown(controller.dispose);
    await controller.refresh();
    await controller.openRevision('rev-1');

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: RevisionReviewPage(controller: controller)),
      ),
    );

    expect(find.text('model original'), findsOneWidget);
    await tester.enterText(
      find.byKey(const Key('revision-edited-text')),
      'edited by tester',
    );
    await tester.tap(find.byKey(const Key('revision-save')));
    await tester.pumpAndSettle();
    expect(httpClient.saved, isTrue);

    await tester.tap(
      find.byKey(const Key('revision-dataset-candidate-toggle')),
    );
    await tester.pumpAndSettle();
    expect(httpClient.candidateMarked, isTrue);
  });

  testWidgets('revision_system capability flag controls navigation entry', (
    tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(900, 1000));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: buildShellNavigation(
            selectedIndex: 0,
            onSelected: (_) {},
            showNovelStudio: true,
            showRevisionReview: false,
          ),
        ),
      ),
    );
    expect(find.text('修订版本'), findsNothing);

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: buildShellNavigation(
            selectedIndex: 0,
            onSelected: (_) {},
            showNovelStudio: true,
            showRevisionReview: true,
          ),
        ),
      ),
    );
    expect(find.text('修订版本'), findsOneWidget);
  });
}
