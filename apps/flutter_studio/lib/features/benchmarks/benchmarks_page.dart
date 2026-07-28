import 'package:flutter/material.dart';

class BenchmarksPage extends StatelessWidget {
  const BenchmarksPage({super.key, required this.benchmarks, required this.currentModel, required this.onStart, required this.onRefresh});

  final List<dynamic> benchmarks;
  final Map<String, dynamic>? currentModel;
  final VoidCallback onStart;
  final VoidCallback onRefresh;

  @override
  Widget build(BuildContext context) {
    final loaded = currentModel?['loaded'] == true;
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          const Text('Benchmark', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
          const Spacer(),
          IconButton.filledTonal(onPressed: onRefresh, icon: const Icon(Icons.refresh), tooltip: 'Refresh'),
        ]),
        const SizedBox(height: 8),
        const Text('Experimental: results are for local development reference only.'),
        const SizedBox(height: 12),
        FilledButton.icon(onPressed: loaded ? onStart : null, icon: const Icon(Icons.speed), label: const Text('Start benchmark for current model')),
        const SizedBox(height: 12),
        Expanded(
          child: benchmarks.isEmpty
              ? const Center(child: Text('No benchmark reports yet.'))
              : ListView.separated(
                  itemCount: benchmarks.length,
                  separatorBuilder: (_, _) => const Divider(height: 1),
                  itemBuilder: (context, index) {
                    final map = benchmarks[index] is Map ? benchmarks[index] as Map : const {};
                    return ListTile(
                      leading: const Icon(Icons.query_stats),
                      title: Text('${map['model_id'] ?? map['id'] ?? 'benchmark'}'),
                      subtitle: Text('TTFT: ${map['ttft_seconds'] ?? 'n/a'}  Token/s: ${map['tokens_per_second'] ?? 'n/a'}  peak: ${map['peak_cuda_reserved'] ?? map['peak_vram'] ?? 'n/a'}'),
                    );
                  },
                ),
        ),
      ]),
    );
  }
}
