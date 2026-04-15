import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../core/api_client.dart';

class ProgressScreen extends ConsumerStatefulWidget {
  const ProgressScreen({super.key});

  @override
  ConsumerState<ProgressScreen> createState() => _ProgressScreenState();
}

class _ProgressScreenState extends ConsumerState<ProgressScreen> {
  Map<String, dynamic>? _progress;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final api = ref.read(apiClientProvider);
    final prefs = await SharedPreferences.getInstance();
    final userId = prefs.getString('user_id') ?? 'default';
    final data = await api.fetchProgress(userId);
    setState(() => _progress = data);
  }

  @override
  Widget build(BuildContext context) {
    if (_progress == null) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    final history = List<Map<String, dynamic>>.from(_progress!['history'] ?? []);
    final actionStatus = Map<String, dynamic>.from(_progress!['action_status'] ?? {});
    return Scaffold(
      appBar: AppBar(title: const Text('Progress')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Card(
            child: ListTile(
              title: const Text('Weekly insight'),
              subtitle: Text((_progress!['insight'] ?? '').toString()),
            ),
          ),
          Card(
            child: ListTile(
              title: const Text('Connections and streak'),
              subtitle: Text(
                'Total connections: ${_progress!['total_connections']} | Streak: ${_progress!['streak']}',
              ),
            ),
          ),
          Card(
            child: ListTile(
              title: const Text('Action lifecycle'),
              subtitle: Text(
                'Completed: ${actionStatus['completed'] ?? 0}, Pending: ${actionStatus['pending'] ?? 0}, Blocked: ${actionStatus['blocked'] ?? 0}',
              ),
            ),
          ),
          const SizedBox(height: 8),
          Text('Score timeline', style: Theme.of(context).textTheme.titleMedium),
          ...history.map((point) => ListTile(
                dense: true,
                title: Text('${point['date']}'),
                subtitle: Text('Score ${point['score']} | Connections ${point['connections']}'),
              )),
        ],
      ),
    );
  }
}
