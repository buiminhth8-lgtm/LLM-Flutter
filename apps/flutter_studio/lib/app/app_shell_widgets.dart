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

class TopBar extends StatelessWidget {
  const TopBar({
    super.key,
    required this.loading,
    required this.backendStatus,
    required this.onRefresh,
  });

  final bool loading;
  final String backendStatus;
  final VoidCallback onRefresh;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 64,
      padding: const EdgeInsets.symmetric(horizontal: 20),
      alignment: Alignment.centerLeft,
      color: Colors.white,
      child: Row(
        children: [
          const Text(
            'LLM Studio',
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.w700),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              backendStatus,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(color: Colors.black54),
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
            tooltip: 'Refresh',
          ),
        ],
      ),
    );
  }
}
