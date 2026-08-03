import 'package:flutter/material.dart';

import '../models/adapter_eval_create_request_dto.dart';
import '../models/adapter_eval_result_dto.dart';

class AdapterEvalRevisionButton extends StatelessWidget {
  const AdapterEvalRevisionButton({
    super.key,
    required this.result,
    required this.projectId,
    this.chapterId,
    required this.onCreate,
  });

  final AdapterEvalResultDto result;
  final String projectId;
  final String? chapterId;
  final void Function(
    String resultId,
    CreateRevisionFromEvalResultRequest request,
  )
  onCreate;

  @override
  Widget build(BuildContext context) {
    return OutlinedButton(
      key: Key('adapter-eval-create-revision-${result.variant}'),
      onPressed: result.status == 'succeeded'
          ? () => onCreate(
              result.resultId,
              CreateRevisionFromEvalResultRequest(
                projectId: projectId,
                chapterId: chapterId,
                editTags: const ['style_unify'],
                userScore: 4,
                qualityNotes: 'Created from Adapter Evaluation.',
              ),
            )
          : null,
      child: Text('Create Revision from ${result.variant}'),
    );
  }
}
