import 'package:flutter/material.dart';

import 'app_shell_widgets.dart';

const novelStudioPageIndex = 9;
const novelProjectsPageIndex = 10;
const promptStudioPageIndex = 11;
const contextAssemblerPageIndex = 12;
const writingWorkspacePageIndex = 13;
const revisionReviewPageIndex = 14;
const datasetBuilderPageIndex = 15;
const finetuneCenterPageIndex = 16;
const adapterEvaluationPageIndex = 17;
const memoryCenterPageIndex = 18;
const evaluationCenterPageIndex = 19;
const settingsPageIndex = 20;

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
    label: '核心',
    destinations: [
      ShellDestination(
        index: 0,
        icon: Icons.monitor_heart_outlined,
        label: '状态',
      ),
      ShellDestination(index: 1, icon: Icons.storage_outlined, label: '模型'),
      ShellDestination(index: 2, icon: Icons.chat_bubble_outline, label: '聊天'),
    ],
  ),
  ShellDestinationGroup(
    label: '工作流',
    destinations: [
      ShellDestination(
        index: 3,
        icon: Icons.cloud_download_outlined,
        label: '下载',
      ),
      ShellDestination(index: 4, icon: Icons.article_outlined, label: 'RAG'),
      ShellDestination(index: 5, icon: Icons.extension_outlined, label: '适配器'),
      ShellDestination(index: 6, icon: Icons.speed_outlined, label: '基准测试'),
    ],
  ),
  ShellDestinationGroup(
    label: '系统',
    destinations: [
      ShellDestination(
        index: 7,
        icon: Icons.cleaning_services_outlined,
        label: '存储',
      ),
      ShellDestination(index: 8, icon: Icons.bug_report_outlined, label: '诊断'),
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
        const SideNavSection(label: '创作'),
        SideNavItem(
          index: novelStudioPageIndex,
          selectedIndex: selectedIndex,
          icon: Icons.auto_stories_outlined,
          label: '小说工作台',
          onSelected: onSelected,
        ),
        SideNavItem(
          index: novelProjectsPageIndex,
          selectedIndex: selectedIndex,
          icon: Icons.library_books_outlined,
          label: '项目',
          onSelected: onSelected,
        ),
        if (showPromptStudio)
          SideNavItem(
            index: promptStudioPageIndex,
            selectedIndex: selectedIndex,
            icon: Icons.description_outlined,
            label: '提示词工作室',
            onSelected: onSelected,
          ),
        if (showContextAssembler)
          SideNavItem(
            index: contextAssemblerPageIndex,
            selectedIndex: selectedIndex,
            icon: Icons.account_tree_outlined,
            label: '上下文预览',
            onSelected: onSelected,
          ),
        if (showWritingWorkspace)
          SideNavItem(
            index: writingWorkspacePageIndex,
            selectedIndex: selectedIndex,
            icon: Icons.edit_note_outlined,
            label: '写作',
            onSelected: onSelected,
          ),
        if (showRevisionReview)
          SideNavItem(
            index: revisionReviewPageIndex,
            selectedIndex: selectedIndex,
            icon: Icons.rate_review_outlined,
            label: '修订版本',
            onSelected: onSelected,
          ),
        if (showDatasetBuilder)
          SideNavItem(
            index: datasetBuilderPageIndex,
            selectedIndex: selectedIndex,
            icon: Icons.dataset_outlined,
            label: '数据集',
            onSelected: onSelected,
          ),
        if (showFinetuneCenter)
          SideNavItem(
            index: finetuneCenterPageIndex,
            selectedIndex: selectedIndex,
            icon: Icons.memory_outlined,
            label: '微调',
            onSelected: onSelected,
          ),
        if (showAdapterEvaluation)
          SideNavItem(
            index: adapterEvaluationPageIndex,
            selectedIndex: selectedIndex,
            icon: Icons.compare_outlined,
            label: '适配器评估',
            onSelected: onSelected,
          ),
        if (showMemoryCenter)
          SideNavItem(
            index: memoryCenterPageIndex,
            selectedIndex: selectedIndex,
            icon: Icons.psychology_alt_outlined,
            label: '记忆',
            onSelected: onSelected,
          ),
        if (showEvaluationCenter)
          SideNavItem(
            index: evaluationCenterPageIndex,
            selectedIndex: selectedIndex,
            icon: Icons.fact_check_outlined,
            label: '评估',
            onSelected: onSelected,
          ),
      ],
      const Divider(),
      SideNavItem(
        index: settingsPageIndex,
        selectedIndex: selectedIndex,
        icon: Icons.settings_outlined,
        label: '设置',
        onSelected: onSelected,
      ),
    ],
  );
}
