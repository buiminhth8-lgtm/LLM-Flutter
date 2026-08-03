import 'package:flutter/material.dart';

class SideNavItem extends StatelessWidget {
  const SideNavItem({
    super.key,
    required this.index,
    required this.selectedIndex,
    required this.icon,
    required this.label,
    required this.onSelected,
  });

  final int index;
  final int selectedIndex;
  final IconData icon;
  final String label;
  final ValueChanged<int> onSelected;

  @override
  Widget build(BuildContext context) {
    final selected = index == selectedIndex;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: ListTile(
        dense: true,
        selected: selected,
        selectedTileColor: const Color(0xffdbeafe),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        leading: Icon(icon),
        title: Text(label),
        onTap: () => onSelected(index),
      ),
    );
  }
}

class SideNavSection extends StatelessWidget {
  const SideNavSection({super.key, required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(12, 14, 12, 6),
      child: Text(
        label,
        style: Theme.of(context).textTheme.labelSmall?.copyWith(
          color: Theme.of(context).colorScheme.onSurfaceVariant,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}

class TopBar extends StatelessWidget {
  const TopBar({
    super.key,
    required this.loading,
    required this.backendStatus,
    required this.modelLabel,
    required this.adapterLabel,
    required this.gpuLabel,
    required this.runningJobs,
    required this.onRefresh,
  });

  final bool loading;
  final String backendStatus;
  final String modelLabel;
  final String adapterLabel;
  final String gpuLabel;
  final int runningJobs;
  final VoidCallback onRefresh;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Container(
      constraints: const BoxConstraints(minHeight: 72),
      padding: const EdgeInsets.symmetric(horizontal: 20),
      alignment: Alignment.centerLeft,
      color: scheme.surface,
      child: Row(
        children: [
          const Text(
            'LLM Studio',
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.w700),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Wrap(
              spacing: 8,
              runSpacing: 6,
              children: [
                _TopPill(
                  icon: Icons.dns_outlined,
                  label: '后端',
                  value: backendStatus,
                ),
                _TopPill(
                  icon: Icons.memory_outlined,
                  label: '模型',
                  value: modelLabel,
                ),
                _TopPill(
                  icon: Icons.extension_outlined,
                  label: '适配器',
                  value: adapterLabel,
                ),
                _TopPill(
                  icon: Icons.bolt_outlined,
                  label: 'GPU',
                  value: gpuLabel,
                ),
                _TopPill(
                  icon: Icons.task_alt_outlined,
                  label: '任务',
                  value: '$runningJobs 个运行中',
                ),
              ],
            ),
          ),
          if (loading)
            const SizedBox(
              width: 20,
              height: 20,
              child: CircularProgressIndicator(strokeWidth: 2),
            ),
          const SizedBox(width: 12),
          IconButton.filledTonal(
            onPressed: loading ? null : onRefresh,
            icon: const Icon(Icons.refresh),
            tooltip: '刷新',
          ),
        ],
      ),
    );
  }
}

class _TopPill extends StatelessWidget {
  const _TopPill({
    required this.icon,
    required this.label,
    required this.value,
  });

  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return DecoratedBox(
      decoration: BoxDecoration(
        color: scheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        child: SizedBox(
          width: 176,
          child: Row(
            children: [
              Icon(icon, size: 15, color: scheme.onSurfaceVariant),
              const SizedBox(width: 5),
              Flexible(
                child: Text(
                  '$label: $value',
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    color: scheme.onSurfaceVariant,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
