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
      return const Center(child: Text('Select an adapter evaluation session.'));
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
                Text('session_id: ${session.sessionId}'),
                Text('base_model_id: ${session.baseModelId}'),
                Text('adapter_id: ${session.adapterId}'),
                Text('dataset_version_id: ${session.datasetVersionId ?? '-'}'),
                Text('finetune_run_id: ${session.finetuneRunId ?? '-'}'),
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
                      label: const Text('Add Case'),
                    ),
                    FilledButton.icon(
                      key: const Key('adapter-eval-run-session'),
                      onPressed: state.loading || session.cases.isEmpty
                          ? null
                          : controller.runCurrentSession,
                      icon: const Icon(Icons.compare_arrows_outlined),
                      label: const Text('Run Session'),
                    ),
                    OutlinedButton.icon(
                      key: const Key('adapter-eval-generate-report'),
                      onPressed: state.loading || session.cases.isEmpty
                          ? null
                          : controller.generateReport,
                      icon: const Icon(Icons.summarize_outlined),
                      label: const Text('Generate Report'),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 8),
        Text('Cases', style: Theme.of(context).textTheme.titleMedium),
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
