import 'dart:async';

import 'package:flutter/material.dart';

import '../../core/ui/app_section_header.dart';
import '../datasets/dataset_controller.dart';
import '../datasets/widgets/revision_to_sample_dialog.dart';
import 'models/revision_record_dto.dart';
import 'revision_controller.dart';
import 'widgets/revision_autosave_indicator.dart';
import 'widgets/revision_dataset_candidate_toggle.dart';
import 'widgets/revision_diff_view.dart';
import 'widgets/revision_editor.dart';
import 'widgets/revision_score_selector.dart';
import 'widgets/revision_status_badge.dart';
import 'widgets/revision_tag_selector.dart';

class RevisionReviewPage extends StatefulWidget {
  const RevisionReviewPage({
    super.key,
    required this.controller,
    this.datasetController,
    this.onOpenDatasetSample,
    this.onEvaluateRevision,
  });

  final RevisionController controller;
  final DatasetController? datasetController;
  final ValueChanged<String>? onOpenDatasetSample;
  final ValueChanged<String>? onEvaluateRevision;

  @override
  State<RevisionReviewPage> createState() => _RevisionReviewPageState();
}

class _RevisionReviewPageState extends State<RevisionReviewPage> {
  final _edited = TextEditingController();
  final _notes = TextEditingController();
  final _projectFilter = TextEditingController();
  final _chapterFilter = TextEditingController();
  String? _syncedRevisionId;

  @override
  void initState() {
    super.initState();
    if (widget.controller.state.revisions.isEmpty) {
      unawaited(widget.controller.refresh());
    }
  }

  @override
  void dispose() {
    unawaited(widget.controller.flushAutosave(_edited.text));
    _edited.dispose();
    _notes.dispose();
    _projectFilter.dispose();
    _chapterFilter.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AnimatedBuilder(
    animation: widget.controller,
    builder: (context, _) {
      final state = widget.controller.state;
      _syncCurrent(state.current);
      return Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            AppSectionHeader(
              title: 'Revision Review',
              subtitle: 'Stage 5：人工修订、Diff、评分、审核和数据集候选标记。',
              actions: [
                RevisionAutosaveIndicator(
                  autosaving: state.autosaving,
                  lastAutosaveAt: state.lastAutosaveAt,
                ),
                IconButton.filledTonal(
                  onPressed: state.loading ? null : widget.controller.refresh,
                  icon: const Icon(Icons.refresh),
                  tooltip: 'Refresh',
                ),
              ],
            ),
            if (state.loading || state.saving) const LinearProgressIndicator(),
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
                  SizedBox(width: 300, child: _buildListPane(state.revisions)),
                  const VerticalDivider(width: 24),
                  Expanded(child: _buildCenterPane(state.current)),
                  const VerticalDivider(width: 24),
                  SizedBox(width: 330, child: _buildMetaPane(state.current)),
                ],
              ),
            ),
          ],
        ),
      );
    },
  );

  Widget _buildListPane(List<RevisionRecordDto> revisions) => ListView(
    children: [
      TextField(
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
      TextField(
        controller: _chapterFilter,
        decoration: const InputDecoration(
          labelText: 'Chapter filter',
          border: OutlineInputBorder(),
        ),
        onSubmitted: (value) => widget.controller.setFilters(
          chapterId: value.trim().isEmpty ? null : value.trim(),
          clearChapter: value.trim().isEmpty,
        ),
      ),
      const SizedBox(height: 8),
      DropdownButtonFormField<String>(
        initialValue: widget.controller.state.selectedStatus,
        decoration: const InputDecoration(
          labelText: 'Status',
          border: OutlineInputBorder(),
        ),
        items: const [
          DropdownMenuItem(value: null, child: Text('All')),
          DropdownMenuItem(value: 'draft', child: Text('draft')),
          DropdownMenuItem(value: 'reviewing', child: Text('reviewing')),
          DropdownMenuItem(value: 'approved', child: Text('approved')),
          DropdownMenuItem(value: 'rejected', child: Text('rejected')),
          DropdownMenuItem(value: 'archived', child: Text('archived')),
        ],
        onChanged: (value) => widget.controller.setFilters(
          status: value,
          clearStatus: value == null,
        ),
      ),
      const SizedBox(height: 8),
      DropdownButtonFormField<int>(
        initialValue: widget.controller.state.selectedScore,
        decoration: const InputDecoration(
          labelText: 'Score',
          border: OutlineInputBorder(),
        ),
        items: const [
          DropdownMenuItem(value: null, child: Text('All')),
          DropdownMenuItem(value: 1, child: Text('1')),
          DropdownMenuItem(value: 2, child: Text('2')),
          DropdownMenuItem(value: 3, child: Text('3')),
          DropdownMenuItem(value: 4, child: Text('4')),
          DropdownMenuItem(value: 5, child: Text('5')),
        ],
        onChanged: (value) => widget.controller.setFilters(
          score: value,
          clearScore: value == null,
        ),
      ),
      const SizedBox(height: 12),
      for (final revision in revisions)
        ListTile(
          key: Key('revision-row-${revision.revisionId}'),
          dense: true,
          selected:
              widget.controller.state.current?.revisionId ==
              revision.revisionId,
          leading: const Icon(Icons.rate_review_outlined),
          title: Text(
            revision.generationId == null
                ? revision.source
                : 'Generation ${revision.generationId}',
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          subtitle: Text(
            '${revision.status} · score ${revision.userScore ?? '-'}',
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
          onTap: () => widget.controller.openRevision(revision.revisionId),
        ),
    ],
  );

  Widget _buildCenterPane(RevisionRecordDto? revision) {
    if (revision == null) {
      return const Center(child: Text('Select a revision to review.'));
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Expanded(
          flex: 3,
          child: RevisionEditor(
            originalText: revision.originalText,
            editedController: _edited,
            onChanged: widget.controller.scheduleAutosave,
          ),
        ),
        const SizedBox(height: 12),
        Expanded(flex: 2, child: RevisionDiffView(diff: revision.diff)),
      ],
    );
  }

  Widget _buildMetaPane(RevisionRecordDto? revision) {
    final state = widget.controller.state;
    if (revision == null) {
      return const Center(child: Text('No revision selected.'));
    }
    return ListView(
      children: [
        Row(
          children: [
            RevisionStatusBadge(status: revision.status),
            const Spacer(),
            Text(revision.source),
          ],
        ),
        const SizedBox(height: 12),
        RevisionTagSelector(
          values: state.editTags,
          onChanged: widget.controller.setTags,
        ),
        const SizedBox(height: 14),
        RevisionScoreSelector(
          value: state.userScore,
          onChanged: widget.controller.setScore,
        ),
        const SizedBox(height: 12),
        TextField(
          key: const Key('revision-quality-notes'),
          controller: _notes,
          minLines: 4,
          maxLines: 7,
          onChanged: widget.controller.setQualityNotes,
          decoration: const InputDecoration(
            labelText: 'Quality notes',
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 12),
        RevisionDatasetCandidateToggle(
          value: state.acceptedForDataset,
          onChanged: widget.controller.setDatasetCandidate,
        ),
        const SizedBox(height: 8),
        OutlinedButton.icon(
          key: const Key('revision-evaluate-revision'),
          onPressed: () => widget.onEvaluateRevision?.call(revision.revisionId),
          icon: const Icon(Icons.fact_check_outlined),
          label: const Text('Evaluate Revision'),
        ),
        if (widget.datasetController != null) ...[
          const SizedBox(height: 8),
          OutlinedButton.icon(
            key: const Key('revision-add-to-dataset'),
            onPressed: () => _addToDataset(revision),
            icon: const Icon(Icons.dataset_outlined),
            label: const Text('Add to Dataset'),
          ),
          const SizedBox(height: 8),
          OutlinedButton.icon(
            key: const Key('revision-create-sft-sample'),
            onPressed: () => _addToDataset(revision),
            icon: const Icon(Icons.playlist_add_outlined),
            label: const Text('Create SFT Sample'),
          ),
        ],
        const SizedBox(height: 14),
        FilledButton.icon(
          key: const Key('revision-save'),
          onPressed: state.saving
              ? null
              : () => widget.controller.saveCurrent(_edited.text),
          icon: const Icon(Icons.save_outlined),
          label: const Text('Save Revision'),
        ),
        const SizedBox(height: 8),
        OutlinedButton.icon(
          key: const Key('revision-approve'),
          onPressed: widget.controller.approveCurrent,
          icon: const Icon(Icons.verified_outlined),
          label: const Text('Approve'),
        ),
        const SizedBox(height: 8),
        OutlinedButton.icon(
          key: const Key('revision-reject'),
          onPressed: () =>
              widget.controller.rejectCurrent(reason: _notes.text.trim()),
          icon: const Icon(Icons.block_outlined),
          label: const Text('Reject'),
        ),
      ],
    );
  }

  void _syncCurrent(RevisionRecordDto? revision) {
    if (revision == null || _syncedRevisionId == revision.revisionId) {
      return;
    }
    _syncedRevisionId = revision.revisionId;
    _edited.text = revision.editedText;
    _notes.text = revision.qualityNotes ?? '';
  }

  Future<void> _addToDataset(RevisionRecordDto revision) async {
    final datasets = widget.datasetController;
    if (datasets == null) {
      return;
    }
    await datasets.refresh();
    if (!mounted) {
      return;
    }
    final datasetId = await showDialog<String>(
      context: context,
      builder: (_) => RevisionToSampleDialog(
        datasets: datasets.state.datasets,
        revisionAccepted: revision.acceptedForDataset,
        revisionApproved: revision.status == 'approved',
      ),
    );
    if (datasetId == null) {
      return;
    }
    final sample = await datasets.createSampleFromRevision(
      datasetId: datasetId,
      revisionId: revision.revisionId,
      sampleType: 'sft',
    );
    if (sample != null) {
      widget.onOpenDatasetSample?.call(sample.sampleId);
    }
  }
}
