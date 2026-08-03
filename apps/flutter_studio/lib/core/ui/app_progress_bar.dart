import 'package:flutter/material.dart';

class AppProgressBar extends StatelessWidget {
  const AppProgressBar({super.key, this.value, this.label});

  final double? value;
  final String? label;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        LinearProgressIndicator(value: value),
        if (label != null) ...[
          const SizedBox(height: 6),
          Text(label!, style: Theme.of(context).textTheme.bodySmall),
        ],
      ],
    );
  }
}
