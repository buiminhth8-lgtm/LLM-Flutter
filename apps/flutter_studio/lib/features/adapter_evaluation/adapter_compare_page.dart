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
      return const Center(child: Text('请选择用例以对比输出。'));
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
                Text('用例 ID：${caseDto.caseId}'),
                Text('模式：${caseDto.mode}'),
                Text('?? ID?${caseDto.templateId ?? '-'}'),
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
                      label: const Text('运行用例'),
                    ),
                    OutlinedButton.icon(
                      key: const Key('adapter-eval-refresh-case'),
                      onPressed: state.loading
                          ? null
                          : () => controller.selectCase(caseDto.caseId),
                      icon: const Icon(Icons.refresh_outlined),
                      label: const Text('刷新用例'),
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
                  Text('修订交接', style: Theme.of(context).textTheme.titleMedium),
                  const Text('从选定输出创建阶段 5 修订候选，不会创建训练样本。'),
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
          title: const Text('提示词 / 上下文快照'),
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
