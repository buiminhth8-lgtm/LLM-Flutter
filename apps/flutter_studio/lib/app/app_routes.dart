import 'package:flutter/material.dart';

import 'app_shell_widgets.dart';

const novelStudioPageIndex = 9;
const promptStudioPageIndex = 10;
const contextAssemblerPageIndex = 11;
const writingWorkspacePageIndex = 12;
const revisionReviewPageIndex = 13;
const datasetBuilderPageIndex = 14;
const finetuneCenterPageIndex = 15;
const adapterEvaluationPageIndex = 16;
const memoryCenterPageIndex = 17;
const evaluationCenterPageIndex = 18;
const settingsPageIndex = 19;

class ShellDestination {
  const ShellDestination({
    required this.index,
    required this.icon,
    required this.label,
  });

  final int index;
  final IconData icon;
  final String label;
}

class ShellDestinationGroup {
  const ShellDestinationGroup({
    required this.label,
    required this.destinations,
  });

  final String label;
  final List<ShellDestination> destinations;
}

const shellDestinationGroups = [
  ShellDestinationGroup(
    label: 'Core',
    destinations: [
      ShellDestination(
        index: 0,
        icon: Icons.monitor_heart_outlined,
        label: 'Status',
      ),
      ShellDestination(index: 1, icon: Icons.storage_outlined, label: 'Models'),
      ShellDestination(
        index: 2,
        icon: Icons.chat_bubble_outline,
        label: 'Chat',
      ),
    ],
  ),
  ShellDestinationGroup(
    label: 'Workflows',
    destinations: [
      ShellDestination(
        index: 3,
        icon: Icons.cloud_download_outlined,
        label: 'Downloads',
      ),
      ShellDestination(index: 4, icon: Icons.article_outlined, label: 'RAG'),
      ShellDestination(
        index: 5,
        icon: Icons.extension_outlined,
        label: 'Adapters',
      ),
      ShellDestination(
        index: 6,
        icon: Icons.speed_outlined,
        label: 'Benchmark',
      ),
    ],
  ),
  ShellDestinationGroup(
    label: 'System',
    destinations: [
      ShellDestination(
        index: 7,
        icon: Icons.cleaning_services_outlined,
        label: 'Storage',
      ),
      ShellDestination(
        index: 8,
        icon: Icons.bug_report_outlined,
        label: 'Diagnostics',
      ),
    ],
  ),
];

Widget buildShellNavigation({
  required int selectedIndex,
  required ValueChanged<int> onSelected,
  bool showNovelStudio = false,
  bool showPromptStudio = false,
  bool showContextAssembler = false,
  bool showWritingWorkspace = false,
  bool showRevisionReview = false,
  bool showDatasetBuilder = false,
  bool showFinetuneCenter = false,
  bool showAdapterEvaluation = false,
  bool showMemoryCenter = false,
  bool showEvaluationCenter = false,
}) {
  return ListView(
    padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
    children: [
      for (final group in shellDestinationGroups) ...[
        SideNavSection(label: group.label),
        for (final destination in group.destinations)
          SideNavItem(
            index: destination.index,
            selectedIndex: selectedIndex,
            icon: destination.icon,
            label: destination.label,
            onSelected: onSelected,
          ),
      ],
      if (showNovelStudio) ...[
        const SideNavSection(label: 'Creative'),
        SideNavItem(
          index: novelStudioPageIndex,
          selectedIndex: selectedIndex,
          icon: Icons.auto_stories_outlined,
          label: 'Novel Studio',
          onSelected: onSelected,
        ),
        if (showPromptStudio)
          SideNavItem(
            index: promptStudioPageIndex,
            selectedIndex: selectedIndex,
            icon: Icons.description_outlined,
            label: 'Prompt Studio',
            onSelected: onSelected,
          ),
        if (showContextAssembler)
          SideNavItem(
            index: contextAssemblerPageIndex,
            selectedIndex: selectedIndex,
            icon: Icons.account_tree_outlined,
            label: 'Context Preview',
            onSelected: onSelected,
          ),
        if (showWritingWorkspace)
          SideNavItem(
            index: writingWorkspacePageIndex,
            selectedIndex: selectedIndex,
            icon: Icons.edit_note_outlined,
            label: 'Writing',
            onSelected: onSelected,
          ),
        if (showRevisionReview)
          SideNavItem(
            index: revisionReviewPageIndex,
            selectedIndex: selectedIndex,
            icon: Icons.rate_review_outlined,
            label: 'Revision',
            onSelected: onSelected,
          ),
        if (showDatasetBuilder)
          SideNavItem(
            index: datasetBuilderPageIndex,
            selectedIndex: selectedIndex,
            icon: Icons.dataset_outlined,
            label: 'Dataset',
            onSelected: onSelected,
          ),
        if (showFinetuneCenter)
          SideNavItem(
            index: finetuneCenterPageIndex,
            selectedIndex: selectedIndex,
            icon: Icons.memory_outlined,
            label: 'Fine-tune',
            onSelected: onSelected,
          ),
        if (showAdapterEvaluation)
          SideNavItem(
            index: adapterEvaluationPageIndex,
            selectedIndex: selectedIndex,
            icon: Icons.compare_outlined,
            label: 'Adapter Eval',
            onSelected: onSelected,
          ),
        if (showMemoryCenter)
          SideNavItem(
            index: memoryCenterPageIndex,
            selectedIndex: selectedIndex,
            icon: Icons.psychology_alt_outlined,
            label: 'Memory',
            onSelected: onSelected,
          ),
        if (showEvaluationCenter)
          SideNavItem(
            index: evaluationCenterPageIndex,
            selectedIndex: selectedIndex,
            icon: Icons.fact_check_outlined,
            label: 'Evaluation',
            onSelected: onSelected,
          ),
      ],
      const Divider(),
      SideNavItem(
        index: settingsPageIndex,
        selectedIndex: selectedIndex,
        icon: Icons.settings_outlined,
        label: 'Settings',
        onSelected: onSelected,
      ),
    ],
  );
}
