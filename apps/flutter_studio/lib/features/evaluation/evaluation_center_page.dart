import 'dart:async';

import 'package:flutter/material.dart';

import '../../core/ui/app_section_header.dart';
import 'evaluation_controller.dart';
import 'evaluation_run_detail_page.dart';
import 'widgets/evaluation_create_run_dialog.dart';
import 'widgets/evaluation_run_list.dart';

class EvaluationCenterPage extends StatefulWidget {
  const EvaluationCenterPage({super.key, required this.controller});

  final EvaluationController controller;

  @override
  State<EvaluationCenterPage> createState() => _EvaluationCenterPageState();
}

class _EvaluationCenterPageState extends State<EvaluationCenterPage> {
  final _projectFilter = TextEditingController();

  @override
  void initState() {
    super.initState();
    if (widget.controller.state.runs.isEmpty) {
      unawaited(widget.controller.refresh());
    }
  }

  @override
  void dispose() {
    _projectFilter.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AnimatedBuilder(
    animation: widget.controller,
    builder: (context, _) {
      final state = widget.controller.state;
      return Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            AppSectionHeader(
              title: 'Evaluation Center',
              subtitle:
                  'Stage 11: automatic heuristics, optional local model judge, findings, manual scores and reports.',
              actions: [
                FilledButton.icon(
                  key: const Key('evaluation-new-run'),
                  onPressed: state.loading ? null : _showCreateRunDialog,
                  icon: const Icon(Icons.add_task_outlined),
                  label: const Text('New Run'),
                ),
                IconButton.filledTonal(
                  onPressed: state.loading ? null : widget.controller.refresh,
                  icon: const Icon(Icons.refresh),
                  tooltip: 'Refresh',
                ),
              ],
            ),
            if (state.loading || state.running || state.saving)
              const LinearProgressIndicator(),
            if (state.error != null)
              MaterialBanner(
                content: Text(state.error!),
                leading: const Icon(Icons.error_outline),
                actions: const [SizedBox.shrink()],
              ),
            if (state.notice != null)
              MaterialBanner(
                content: Text(state.notice!),
                leading: const Icon(Icons.info_outline),
                actions: const [SizedBox.shrink()],
              ),
            const SizedBox(height: 12),
            Expanded(
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  SizedBox(width: 320, child: _buildLeftPane()),
                  const VerticalDivider(width: 24),
                  Expanded(
                    child: EvaluationRunDetailPage(
                      controller: widget.controller,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      );
    },
  );

  Widget _buildLeftPane() {
    final state = widget.controller.state;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        TextField(
          key: const Key('evaluation-project-filter'),
          controller: _projectFilter,
          decoration: const InputDecoration(
            labelText: 'Project filter',
            border: OutlineInputBorder(),
          ),
          onSubmitted: (value) => widget.controller.setFilters(
            projectId: value.trim().isEmpty ? null : value.trim(),
            clearProject: value.trim().isEmpty,
          ),
        ),
        const SizedBox(height: 8),
        DropdownButtonFormField<String>(
          key: const Key('evaluation-target-filter'),
          initialValue: state.selectedTargetType,
          isExpanded: true,
          decoration: const InputDecoration(
            labelText: 'Target type',
            border: OutlineInputBorder(),
          ),
          items: const [
            DropdownMenuItem(value: null, child: Text('All')),
            DropdownMenuItem(value: 'project', child: Text('Project')),
            DropdownMenuItem(value: 'chapter', child: Text('Chapter')),
            DropdownMenuItem(value: 'generation', child: Text('Generation')),
            DropdownMenuItem(value: 'revision', child: Text('Revision')),
            DropdownMenuItem(value: 'memory_retrieval', child: Text('Memory')),
            DropdownMenuItem(
              value: 'adapter_eval_session',
              child: Text('Adapter Eval'),
            ),
          ],
          onChanged: (value) => widget.controller.setFilters(
            targetType: value,
            clearTargetType: value == null,
          ),
        ),
        const SizedBox(height: 8),
        DropdownButtonFormField<String>(
          key: const Key('evaluation-status-filter'),
          initialValue: state.selectedStatus,
          isExpanded: true,
          decoration: const InputDecoration(
            labelText: 'Status',
            border: OutlineInputBorder(),
          ),
          items: const [
            DropdownMenuItem(value: null, child: Text('All')),
            DropdownMenuItem(value: 'created', child: Text('created')),
            DropdownMenuItem(value: 'queued', child: Text('queued')),
            DropdownMenuItem(value: 'running', child: Text('running')),
            DropdownMenuItem(value: 'completed', child: Text('completed')),
            DropdownMenuItem(value: 'failed', child: Text('failed')),
            DropdownMenuItem(value: 'cancelled', child: Text('cancelled')),
            DropdownMenuItem(value: 'archived', child: Text('archived')),
          ],
          onChanged: (value) => widget.controller.setFilters(
            status: value,
            clearStatus: value == null,
          ),
        ),
        const SizedBox(height: 10),
        const Text(
          'Boundary: Evaluation Center only reads existing assets. It never creates training samples or rewrites draft/final content.',
        ),
        const SizedBox(height: 8),
        Expanded(
          child: EvaluationRunList(
            runs: state.runs,
            currentRunId: state.currentRun?.runId,
            onSelect: widget.controller.selectRun,
          ),
        ),
      ],
    );
  }

  void _showCreateRunDialog() {
    showDialog<void>(
      context: context,
      builder: (_) => EvaluationCreateRunDialog(
        onCreate: (request) {
          unawaited(widget.controller.createRun(request));
        },
      ),
    );
  }
}
