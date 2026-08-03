import 'package:flutter/material.dart';

import 'adapter_eval_controller.dart';
import 'models/adapter_eval_result_dto.dart';
import 'widgets/adapter_compare_outputs.dart';
import 'widgets/adapter_eval_revision_button.dart';
import 'widgets/adapter_score_panel.dart';

class AdapterComparePage extends StatelessWidget {
  const AdapterComparePage({super.key, required this.controller});

  final AdapterEvalController controller;

  @override
  Widget build(BuildContext context) {
    final state = controller.state;
    final caseDto = state.currentCase;
    if (caseDto == null) {
      return const Center(child: Text('Select a case to compare outputs.'));
    }
    final projectId =
        caseDto.projectId ?? state.currentSession?.projectId ?? '';
    return ListView(
      key: const Key('adapter-compare-page'),
      children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        caseDto.title,
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                    ),
                    Chip(label: Text(caseDto.status)),
                  ],
                ),
                Text('case_id: ${caseDto.caseId}'),
                Text('mode: ${caseDto.mode}'),
                Text('template_id: ${caseDto.templateId ?? '-'}'),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    FilledButton.icon(
                      key: const Key('adapter-eval-run-case'),
                      onPressed: state.loading
                          ? null
                          : controller.runCurrentCase,
                      icon: const Icon(Icons.play_arrow_outlined),
                      label: const Text('Run Case'),
                    ),
                    OutlinedButton.icon(
                      key: const Key('adapter-eval-refresh-case'),
                      onPressed: state.loading
                          ? null
                          : () => controller.selectCase(caseDto.caseId),
                      icon: const Icon(Icons.refresh_outlined),
                      label: const Text('Refresh Case'),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 8),
        AdapterCompareOutputs(results: caseDto.results),
        const SizedBox(height: 8),
        AdapterScorePanel(
          initialScore: caseDto.score,
          onSave: controller.scoreCurrentCase,
        ),
        if (projectId.isNotEmpty &&
            _succeededResults(caseDto.results).isNotEmpty)
          Card(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Revision Handoff',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const Text(
                    'Create a Stage 5 revision candidate from a selected output. This does not create training samples.',
                  ),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 8,
                    children: [
                      for (final result in _succeededResults(caseDto.results))
                        AdapterEvalRevisionButton(
                          result: result,
                          projectId: projectId,
                          chapterId: caseDto.chapterId,
                          onCreate: controller.createRevisionFromResult,
                        ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        const SizedBox(height: 8),
        ExpansionTile(
          title: const Text('Prompt / Context Snapshot'),
          children: [
            Padding(
              padding: const EdgeInsets.all(12),
              child: SelectableText(caseDto.promptRendered ?? ''),
            ),
            Padding(
              padding: const EdgeInsets.all(12),
              child: SelectableText('${caseDto.contextSnapshot}'),
            ),
          ],
        ),
      ],
    );
  }

  List<AdapterEvalResultDto> _succeededResults(
    List<AdapterEvalResultDto> results,
  ) => results.where((item) => item.status == 'succeeded').toList();
}
