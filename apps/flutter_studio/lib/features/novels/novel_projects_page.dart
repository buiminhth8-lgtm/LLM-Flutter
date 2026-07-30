import 'package:flutter/material.dart';

import '../../core/ui/app_confirm_dialog.dart';
import '../../core/ui/app_empty_state.dart';
import '../../core/ui/app_section_header.dart';
import 'novel_controller.dart';

class NovelProjectsPage extends StatefulWidget {
  const NovelProjectsPage({super.key, required this.controller});

  final NovelController controller;

  @override
  State<NovelProjectsPage> createState() => _NovelProjectsPageState();
}

class _NovelProjectsPageState extends State<NovelProjectsPage> {
  final _projectTitle = TextEditingController();
  final _projectGenre = TextEditingController();
  final _projectDescription = TextEditingController();
  final _chapterTitle = TextEditingController();
  final _chapterOutline = TextEditingController();
  final _characterName = TextEditingController();
  final _characterRole = TextEditingController();
  final _worldCategory = TextEditingController(text: 'location');
  final _worldTitle = TextEditingController();
  final _worldContent = TextEditingController();

  @override
  void dispose() {
    _projectTitle.dispose();
    _projectGenre.dispose();
    _projectDescription.dispose();
    _chapterTitle.dispose();
    _chapterOutline.dispose();
    _characterName.dispose();
    _characterRole.dispose();
    _worldCategory.dispose();
    _worldTitle.dispose();
    _worldContent.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = widget.controller.state;
    final selected = state.selectedProject;
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AppSectionHeader(
            title: 'Novel Studio',
            subtitle:
                'Stage 1 foundation: projects, chapters, characters, and world bible. No AI generation is connected.',
            actions: [
              IconButton.filledTonal(
                onPressed: widget.controller.refresh,
                icon: const Icon(Icons.refresh),
                tooltip: 'Refresh',
              ),
            ],
          ),
          const SizedBox(height: 12),
          if (state.error != null)
            MaterialBanner(
              content: Text(state.error!),
              leading: const Icon(Icons.error_outline),
              actions: [
                TextButton(
                  onPressed: () => setState(() {}),
                  child: const Text('Dismiss'),
                ),
              ],
            ),
          Expanded(
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                SizedBox(
                  width: 320,
                  child: _ProjectList(
                    controller: widget.controller,
                    titleController: _projectTitle,
                    genreController: _projectGenre,
                    descriptionController: _projectDescription,
                  ),
                ),
                const VerticalDivider(width: 24),
                Expanded(
                  child: selected == null
                      ? const AppEmptyState(
                          title: 'No novel project',
                          message:
                              'Create a project to start building the foundation library.',
                          icon: Icons.menu_book_outlined,
                        )
                      : NovelProjectDetailPage(
                          controller: widget.controller,
                          chapterTitle: _chapterTitle,
                          chapterOutline: _chapterOutline,
                          characterName: _characterName,
                          characterRole: _characterRole,
                          worldCategory: _worldCategory,
                          worldTitle: _worldTitle,
                          worldContent: _worldContent,
                        ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _ProjectList extends StatelessWidget {
  const _ProjectList({
    required this.controller,
    required this.titleController,
    required this.genreController,
    required this.descriptionController,
  });

  final NovelController controller;
  final TextEditingController titleController;
  final TextEditingController genreController;
  final TextEditingController descriptionController;

  @override
  Widget build(BuildContext context) {
    final state = controller.state;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        TextField(
          controller: titleController,
          decoration: const InputDecoration(
            labelText: 'Project title',
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 8),
        TextField(
          controller: genreController,
          decoration: const InputDecoration(
            labelText: 'Genre',
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 8),
        TextField(
          controller: descriptionController,
          minLines: 2,
          maxLines: 3,
          decoration: const InputDecoration(
            labelText: 'Description',
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 8),
        FilledButton.icon(
          onPressed: () async {
            if (titleController.text.trim().isEmpty) {
              return;
            }
            await controller.createProject(
              title: titleController.text.trim(),
              genre: genreController.text.trim(),
              description: descriptionController.text.trim(),
            );
            titleController.clear();
            genreController.clear();
            descriptionController.clear();
          },
          icon: const Icon(Icons.add),
          label: const Text('Create project'),
        ),
        const SizedBox(height: 16),
        Expanded(
          child: state.projects.isEmpty
              ? const AppEmptyState(
                  title: 'No projects',
                  message: 'Novel projects are stored locally in SQLite.',
                  icon: Icons.menu_book_outlined,
                )
              : ListView.separated(
                  itemCount: state.projects.length,
                  separatorBuilder: (_, _) => const SizedBox(height: 8),
                  itemBuilder: (context, index) {
                    final project = state.projects[index];
                    final selected = project.id == state.selectedProject?.id;
                    return ListTile(
                      selected: selected,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                      tileColor: selected
                          ? Theme.of(context).colorScheme.secondaryContainer
                          : null,
                      title: Text(project.title),
                      subtitle: Text(project.genre ?? project.status),
                      onTap: () => controller.selectProject(project.id),
                    );
                  },
                ),
        ),
      ],
    );
  }
}

class NovelProjectDetailPage extends StatelessWidget {
  const NovelProjectDetailPage({
    super.key,
    required this.controller,
    required this.chapterTitle,
    required this.chapterOutline,
    required this.characterName,
    required this.characterRole,
    required this.worldCategory,
    required this.worldTitle,
    required this.worldContent,
  });

  final NovelController controller;
  final TextEditingController chapterTitle;
  final TextEditingController chapterOutline;
  final TextEditingController characterName;
  final TextEditingController characterRole;
  final TextEditingController worldCategory;
  final TextEditingController worldTitle;
  final TextEditingController worldContent;

  @override
  Widget build(BuildContext context) {
    final state = controller.state;
    final project = state.selectedProject!;
    return DefaultTabController(
      length: 7,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      project.title,
                      style: Theme.of(context).textTheme.headlineSmall,
                    ),
                    Text(project.description ?? 'No description'),
                  ],
                ),
              ),
              OutlinedButton.icon(
                onPressed: () async {
                  final ok = await showAppConfirmDialog(
                    context,
                    title: 'Delete project?',
                    message:
                        'This performs a soft delete. Child records are kept but hidden by default.',
                    confirmLabel: 'Delete project',
                    destructive: true,
                  );
                  if (ok == true) {
                    await controller.deleteSelectedProject();
                  }
                },
                icon: const Icon(Icons.delete_outline),
                label: const Text('Delete project'),
              ),
            ],
          ),
          const SizedBox(height: 12),
          const TabBar(
            isScrollable: true,
            tabs: [
              Tab(text: 'Overview'),
              Tab(text: 'Volumes'),
              Tab(text: 'Chapters'),
              Tab(text: 'Characters'),
              Tab(text: 'World Bible'),
              Tab(text: 'Plot Threads'),
              Tab(text: 'Timeline'),
            ],
          ),
          const SizedBox(height: 12),
          Expanded(
            child: TabBarView(
              children: [
                _Overview(project: project),
                _PlannedPanel(title: 'Volumes', count: state.volumes.length),
                _ChaptersPanel(
                  controller: controller,
                  titleController: chapterTitle,
                  outlineController: chapterOutline,
                ),
                _CharactersPanel(
                  controller: controller,
                  nameController: characterName,
                  roleController: characterRole,
                ),
                _WorldPanel(
                  controller: controller,
                  categoryController: worldCategory,
                  titleController: worldTitle,
                  contentController: worldContent,
                ),
                _PlannedPanel(
                  title: 'Plot Threads',
                  count: state.plotThreads.length,
                ),
                _PlannedPanel(title: 'Timeline', count: state.timeline.length),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _Overview extends StatelessWidget {
  const _Overview({required this.project});

  final dynamic project;

  @override
  Widget build(BuildContext context) {
    return ListView(
      children: [
        ListTile(title: const Text('Slug'), subtitle: Text(project.slug)),
        ListTile(
          title: const Text('Genre'),
          subtitle: Text(project.genre ?? '-'),
        ),
        ListTile(
          title: const Text('Target style'),
          subtitle: Text(project.targetStyle ?? '-'),
        ),
        ListTile(
          title: const Text('Target audience'),
          subtitle: Text(project.targetAudience ?? '-'),
        ),
        const ListTile(
          title: Text('Stage 1 boundary'),
          subtitle: Text(
            'No generation, Prompt Studio, Revision, Dataset, or FineTune workflow is connected.',
          ),
        ),
      ],
    );
  }
}

class _ChaptersPanel extends StatelessWidget {
  const _ChaptersPanel({
    required this.controller,
    required this.titleController,
    required this.outlineController,
  });

  final NovelController controller;
  final TextEditingController titleController;
  final TextEditingController outlineController;

  @override
  Widget build(BuildContext context) {
    final chapters = controller.state.chapters;
    return Column(
      children: [
        Row(
          children: [
            Expanded(
              child: TextField(
                controller: titleController,
                decoration: const InputDecoration(
                  labelText: 'Chapter title',
                  border: OutlineInputBorder(),
                ),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextField(
                controller: outlineController,
                decoration: const InputDecoration(
                  labelText: 'Outline',
                  border: OutlineInputBorder(),
                ),
              ),
            ),
            const SizedBox(width: 8),
            FilledButton(
              onPressed: () async {
                if (titleController.text.trim().isEmpty) {
                  return;
                }
                await controller.createChapter(
                  title: titleController.text.trim(),
                  outline: outlineController.text.trim(),
                );
                titleController.clear();
                outlineController.clear();
              },
              child: const Text('Save draft'),
            ),
          ],
        ),
        const SizedBox(height: 12),
        Expanded(
          child: chapters.isEmpty
              ? const AppEmptyState(
                  title: 'No chapters',
                  message: 'Create chapter outlines and local drafts only.',
                  icon: Icons.article_outlined,
                )
              : ListView(
                  children: [
                    for (final chapter in chapters)
                      ListTile(
                        title: Text(
                          '${chapter.chapterIndex}. ${chapter.title}',
                        ),
                        subtitle: Text(
                          '${chapter.status} / ${chapter.wordCount} words',
                        ),
                      ),
                  ],
                ),
        ),
      ],
    );
  }
}

class _CharactersPanel extends StatelessWidget {
  const _CharactersPanel({
    required this.controller,
    required this.nameController,
    required this.roleController,
  });

  final NovelController controller;
  final TextEditingController nameController;
  final TextEditingController roleController;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Row(
          children: [
            Expanded(
              child: TextField(
                controller: nameController,
                decoration: const InputDecoration(
                  labelText: 'Character name',
                  border: OutlineInputBorder(),
                ),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextField(
                controller: roleController,
                decoration: const InputDecoration(
                  labelText: 'Role',
                  border: OutlineInputBorder(),
                ),
              ),
            ),
            const SizedBox(width: 8),
            FilledButton(
              onPressed: () async {
                if (nameController.text.trim().isEmpty) {
                  return;
                }
                await controller.createCharacter(
                  name: nameController.text.trim(),
                  role: roleController.text.trim(),
                );
                nameController.clear();
                roleController.clear();
              },
              child: const Text('Create character'),
            ),
          ],
        ),
        const SizedBox(height: 12),
        Expanded(
          child: ListView(
            children: [
              for (final character in controller.state.characters)
                ListTile(
                  title: Text(character.name),
                  subtitle: Text(character.role ?? character.status),
                ),
            ],
          ),
        ),
      ],
    );
  }
}

class _WorldPanel extends StatelessWidget {
  const _WorldPanel({
    required this.controller,
    required this.categoryController,
    required this.titleController,
    required this.contentController,
  });

  final NovelController controller;
  final TextEditingController categoryController;
  final TextEditingController titleController;
  final TextEditingController contentController;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Row(
          children: [
            SizedBox(
              width: 160,
              child: TextField(
                controller: categoryController,
                decoration: const InputDecoration(
                  labelText: 'Category',
                  border: OutlineInputBorder(),
                ),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextField(
                controller: titleController,
                decoration: const InputDecoration(
                  labelText: 'Entry title',
                  border: OutlineInputBorder(),
                ),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextField(
                controller: contentController,
                decoration: const InputDecoration(
                  labelText: 'Content',
                  border: OutlineInputBorder(),
                ),
              ),
            ),
            const SizedBox(width: 8),
            FilledButton(
              onPressed: () async {
                if (titleController.text.trim().isEmpty ||
                    contentController.text.trim().isEmpty) {
                  return;
                }
                await controller.createWorldEntry(
                  category: categoryController.text.trim().isEmpty
                      ? 'other'
                      : categoryController.text.trim(),
                  title: titleController.text.trim(),
                  content: contentController.text.trim(),
                );
                titleController.clear();
                contentController.clear();
              },
              child: const Text('Create entry'),
            ),
          ],
        ),
        const SizedBox(height: 12),
        Expanded(
          child: ListView(
            children: [
              for (final entry in controller.state.worldEntries)
                ListTile(
                  title: Text(entry.title),
                  subtitle: Text('${entry.category}: ${entry.content}'),
                ),
            ],
          ),
        ),
      ],
    );
  }
}

class _PlannedPanel extends StatelessWidget {
  const _PlannedPanel({required this.title, required this.count});

  final String title;
  final int count;

  @override
  Widget build(BuildContext context) {
    return AppEmptyState(
      title: '$title planned',
      message:
          'API/DTO foundation exists. Full editing UI is planned for a later Stage 1 iteration. Current records: $count.',
      icon: Icons.pending_actions_outlined,
    );
  }
}
