import 'dart:async';

import 'package:flutter/material.dart';

import 'adapter_eval_controller.dart';
import 'models/adapter_eval_create_request_dto.dart';
import 'widgets/adapter_eval_case_list.dart';
import 'widgets/adapter_eval_create_case_dialog.dart';
import 'widgets/adapter_eval_report_panel.dart';

class AdapterEvalSessionDetailPage extends StatelessWidget {
  const AdapterEvalSessionDetailPage({super.key, required this.controller});

  final AdapterEvalController controller;

  @override
  Widget build(BuildContext context) {
    final state = controller.state;
    final session = state.currentSession;
    if (session == null) {
      return const Center(child: Text('请选择适配器评估会话。'));
    }
    return ListView(
      key: const Key('adapter-eval-session-detail'),
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
                        session.name,
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                    ),
                    Chip(label: Text(session.status)),
                  ],
                ),
                Text('会话 ID：${session.sessionId}'),
                Text('基础模型 ID：${session.baseModelId}'),
                Text('适配器 ID：${session.adapterId}'),
                Text('数据集版本 ID：${session.datasetVersionId ?? '-'}'),
                Text('微调任务 ID：${session.finetuneRunId ?? '-'}'),
                if (session.description != null) Text(session.description!),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    OutlinedButton.icon(
                      key: const Key('adapter-eval-add-case'),
                      onPressed: state.loading
                          ? null
                          : () => _showCreateCase(context),
                      icon: const Icon(Icons.note_add_outlined),
                      label: const Text('添加用例'),
                    ),
                    FilledButton.icon(
                      key: const Key('adapter-eval-run-session'),
                      onPressed: state.loading || session.cases.isEmpty
                          ? null
                          : controller.runCurrentSession,
                      icon: const Icon(Icons.compare_arrows_outlined),
                      label: const Text('运行会话'),
                    ),
                    OutlinedButton.icon(
                      key: const Key('adapter-eval-generate-report'),
                      onPressed: state.loading || session.cases.isEmpty
                          ? null
                          : controller.generateReport,
                      icon: const Icon(Icons.summarize_outlined),
                      label: const Text('生成报告'),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 8),
        Text('用例', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 6),
        AdapterEvalCaseList(
          cases: session.cases,
          onSelect: controller.selectCase,
        ),
        const SizedBox(height: 12),
        AdapterEvalReportPanel(reports: state.reports),
      ],
    );
  }

  void _showCreateCase(BuildContext context) {
    final session = controller.state.currentSession;
    showDialog<void>(
      context: context,
      builder: (_) => AdapterEvalCreateCaseDialog(
        projectId: session?.projectId,
        onCreate: (CreateAdapterEvalCaseRequest request) {
          unawaited(controller.createCase(request));
        },
      ),
    );
  }
}
