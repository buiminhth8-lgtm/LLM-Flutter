import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_studio/app/app_routes.dart';
import 'package:flutter_studio/core/api/api_client.dart';
import 'package:flutter_studio/features/datasets/dataset_api_client.dart';
import 'package:flutter_studio/features/datasets/dataset_builder_page.dart';
import 'package:flutter_studio/features/datasets/dataset_controller.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

class DatasetPageHttpClient extends http.BaseClient {
  bool created = false;

  @override
  Future<http.StreamedResponse> send(http.BaseRequest request) async {
    final path = request.url.path;
    Object response = <String, Object?>{};
    if (path == '/v1/datasets') {
      if (request.method == 'POST') {
        created = true;
        response = _dataset(name: 'New Draft');
      } else {
        response = {
          'data': [_dataset()],
        };
      }
    } else if (path == '/v1/datasets/dataset-1') {
      response = _dataset();
    } else if (path == '/v1/datasets/dataset-1/samples') {
      response = {
        'data': [_sample()],
      };
    } else if (path == '/v1/datasets/dataset-1/exports') {
      response = {'data': <Object?>[]};
    }
    return http.StreamedResponse(
      Stream.value(utf8.encode(jsonEncode(response))),
      200,
      headers: {'content-type': 'application/json'},
    );
  }

  Map<String, Object?> _dataset({String name = 'Dataset A'}) => {
    'dataset_id': 'dataset-1',
    'name': name,
    'type': 'sft',
    'status': 'draft',
    'sample_count': 1,
    'approved_sample_count': 0,
    'rejected_sample_count': 0,
    'created_at': 'now',
    'updated_at': 'now',
  };

  Map<String, Object?> _sample() => {
    'sample_id': 'sample-1',
    'dataset_id': 'dataset-1',
    'sample_type': 'sft',
    'instruction': 'inst',
    'input': 'input',
    'output': 'output',
    'source_hash': 's',
    'content_hash': 'c',
    'status': 'pending',
    'created_at': 'now',
    'updated_at': 'now',
  };
}

void main() {
  testWidgets('Dataset Builder page displays list and submits create form', (
    tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(1500, 1000));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    final httpClient = DatasetPageHttpClient();
    final controller = DatasetController(
      DatasetApiClient(
        LlmStudioClient('http://127.0.0.1:8000', httpClient: httpClient),
      ),
    );
    addTearDown(controller.dispose);
    await controller.refresh();

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(body: DatasetBuilderPage(controller: controller)),
      ),
    );

    expect(find.text('Dataset A'), findsOneWidget);
    await tester.tap(find.byKey(const Key('dataset-create-button')));
    await tester.pumpAndSettle();
    await tester.enterText(
      find.byKey(const Key('dataset-name-input')),
      'New Draft',
    );
    await tester.tap(find.byKey(const Key('dataset-create-submit')));
    await tester.pumpAndSettle();
    expect(httpClient.created, isTrue);
  });

  testWidgets('dataset_builder capability flag controls navigation entry', (
    tester,
  ) async {
    await tester.binding.setSurfaceSize(const Size(900, 1200));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: buildShellNavigation(
            selectedIndex: 0,
            onSelected: (_) {},
            showNovelStudio: true,
            showDatasetBuilder: false,
          ),
        ),
      ),
    );
    expect(find.text('Dataset'), findsNothing);

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: buildShellNavigation(
            selectedIndex: 0,
            onSelected: (_) {},
            showNovelStudio: true,
            showDatasetBuilder: true,
          ),
        ),
      ),
    );
    expect(find.text('Dataset'), findsOneWidget);
  });
}
