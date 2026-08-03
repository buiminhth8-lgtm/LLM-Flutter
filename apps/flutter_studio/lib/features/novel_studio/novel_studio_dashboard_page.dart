import 'package:flutter/material.dart';

import '../../core/ui/app_diagnostics_hint.dart';
import '../../core/ui/app_empty_state.dart';
import '../../core/ui/app_section_header.dart';
import 'novel_studio_capability_banner.dart';
import 'novel_studio_route_guard.dart';
import 'widgets/novel_studio_health_panel.dart';
import 'widgets/novel_studio_progress_map.dart';
import 'widgets/novel_studio_quick_actions.dart';
import 'widgets/novel_studio_recent_activity.dart';

class NovelStudioDashboardPage extends StatelessWidget {
  const NovelStudioDashboardPage({
    super.key,
    required this.capabilities,
    required this.projectCount,
    required this.chapterCount,
    required this.generationCount,
    required this.revisionCount,
    required this.datasetCount,
    required this.finetuneRunCount,
    required this.evaluationRunCount,
    required this.backendStatus,
    required this.modelLabel,
    required this.adapterLabel,
    required this.runningJobs,
    required this.onRefresh,
    required this.onOpenProjects,
    required this.onOpenPrompts,
    required this.onOpenContext,
    required this.onOpenWriting,
    required this.onOpenRevisions,
    required this.onOpenDataset,
    required this.onOpenFinetune,
    required this.onOpenAdapterEvaluation,
    required this.onOpenMemory,
    required this.onOpenEvaluation,
    required this.onOpenDiagnostics,
    this.health,
  });

  final List<dynamic> capabilities;
  final int projectCount;
  final int chapterCount;
  final int generationCount;
  final int revisionCount;
  final int datasetCount;
  final int finetuneRunCount;
  final int evaluationRunCount;
  final String backendStatus;
  final String modelLabel;
  final String adapterLabel;
  final int runningJobs;
  final VoidCallback onRefresh;
  final VoidCallback onOpenProjects;
  final VoidCallback onOpenPrompts;
  final VoidCallback onOpenContext;
  final VoidCallback onOpenWriting;
  final VoidCallback onOpenRevisions;
  final VoidCallback onOpenDataset;
  final VoidCallback onOpenFinetune;
  final VoidCallback onOpenAdapterEvaluation;
  final VoidCallback onOpenMemory;
  final VoidCallback onOpenEvaluation;
  final VoidCallback onOpenDiagnostics;
  final Map<String, dynamic>? health;

  @override
  Widget build(BuildContext context) {
    final guard = NovelStudioRouteGuard(capabilities);
    if (!guard.isAvailable('novel_studio')) {
      return AppEmptyState(
        title: 'Novel Studio is disabled',
        message:
            'Enable features.novel_studio.enabled and refresh capabilities.',
        icon: Icons.auto_stories_outlined,
        action: OutlinedButton.icon(
          onPressed: onRefresh,
          icon: const Icon(Icons.refresh),
          label: const Text('Refresh capabilities'),
        ),
      );
    }
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        AppSectionHeader(
          title: 'Novel Studio Dashboard',
          subtitle:
              '从项目资料、Prompt、Context、Writing、Revision、Dataset、Fine-tune、Memory 到 Evaluation 的本地闭环入口。',
          actions: [
            OutlinedButton.icon(
              onPressed: onOpenPrompts,
              icon: const Icon(Icons.description_outlined),
              label: const Text('Prompts'),
            ),
            const SizedBox(width: 8),
            FilledButton.icon(
              onPressed: onOpenProjects,
              icon: const Icon(Icons.add),
              label: const Text('New / Open Project'),
            ),
          ],
        ),
        const SizedBox(height: 12),
        NovelStudioQuickActions(
          onOpenProjects: onOpenProjects,
          onOpenPrompts: onOpenPrompts,
          onOpenContext: onOpenContext,
          onOpenWriting: onOpenWriting,
          onOpenRevisions: onOpenRevisions,
          onOpenDataset: onOpenDataset,
          onOpenFinetune: onOpenFinetune,
          onOpenAdapterEvaluation: onOpenAdapterEvaluation,
          onOpenMemory: onOpenMemory,
          onOpenEvaluation: onOpenEvaluation,
          onOpenDiagnostics: onOpenDiagnostics,
        ),
        const SizedBox(height: 12),
        NovelStudioCapabilityBanner(guard: guard),
        const SizedBox(height: 12),
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(flex: 2, child: NovelStudioProgressMap(guard: guard)),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                children: [
                  NovelStudioHealthPanel(
                    health: health,
                    backendStatus: backendStatus,
                    modelLabel: modelLabel,
                    adapterLabel: adapterLabel,
                    runningJobs: runningJobs,
                    onRefresh: onRefresh,
                  ),
                  const SizedBox(height: 12),
                  NovelStudioRecentActivity(
                    projectCount: projectCount,
                    chapterCount: chapterCount,
                    generationCount: generationCount,
                    revisionCount: revisionCount,
                    datasetCount: datasetCount,
                    finetuneRunCount: finetuneRunCount,
                    evaluationRunCount: evaluationRunCount,
                  ),
                ],
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: _JourneyCard(
                title: 'Authoring path',
                icon: Icons.edit_note_outlined,
                steps: const [
                  'Project → Chapters → Prompt',
                  'Context preview → Writing',
                  'Save to Draft only when you choose it',
                  'Revision stays separate from final_content',
                ],
                onOpen: onOpenWriting,
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _JourneyCard(
                title: 'Improvement path',
                icon: Icons.science_outlined,
                steps: const [
                  'Approved Revision → Dataset',
                  'Freeze DatasetVersion',
                  'Confirm recipe → Fine-tune',
                  'Compare adapters → Evaluation',
                ],
                onOpen: onOpenDataset,
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        AppDiagnosticsHint(onOpenDiagnostics: onOpenDiagnostics),
      ],
    );
  }
}

class _JourneyCard extends StatelessWidget {
  const _JourneyCard({
    required this.title,
    required this.icon,
    required this.steps,
    required this.onOpen,
  });

  final String title;
  final IconData icon;
  final List<String> steps;
  final VoidCallback onOpen;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon),
                const SizedBox(width: 8),
                Text(title, style: Theme.of(context).textTheme.titleMedium),
              ],
            ),
            const SizedBox(height: 12),
            for (final step in steps)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 2),
                child: Text('• $step'),
              ),
            const SizedBox(height: 12),
            OutlinedButton(onPressed: onOpen, child: const Text('Open')),
          ],
        ),
      ),
    );
  }
}
