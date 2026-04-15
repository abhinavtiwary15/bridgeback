import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api_client.dart';
import '../../core/session_provider.dart';

class SettingsScreen extends ConsumerStatefulWidget {
  const SettingsScreen({super.key});

  @override
  ConsumerState<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends ConsumerState<SettingsScreen> {
  late final TextEditingController _userIdCtrl;
  late final TextEditingController _apiUrlCtrl;
  late final TextEditingController _apiKeyCtrl;

  @override
  void initState() {
    super.initState();
    final currentUser = ref.read(userIdProvider);
    _userIdCtrl = TextEditingController(text: currentUser);
    _apiUrlCtrl = TextEditingController();
    _apiKeyCtrl = TextEditingController();
    _loadApiPrefs();
  }

  Future<void> _loadApiPrefs() async {
    final url = await ApiClient.getStoredBaseUrl();
    final key = await ApiClient.getStoredApiKey();
    if (!mounted) return;
    if (url != null && url.isNotEmpty) _apiUrlCtrl.text = url;
    if (key != null && key.isNotEmpty) _apiKeyCtrl.text = key;
  }

  @override
  void dispose() {
    _userIdCtrl.dispose();
    _apiUrlCtrl.dispose();
    _apiKeyCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final userIdNotifier = ref.read(userIdProvider.notifier);

    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: ListView(
          children: [
            const Text('Server URL', style: TextStyle(fontWeight: FontWeight.w600)),
            const SizedBox(height: 8),
            TextField(
              controller: _apiUrlCtrl,
              decoration: const InputDecoration(
                hintText: 'https://your-api.example.com',
                border: OutlineInputBorder(),
              ),
              keyboardType: TextInputType.url,
              autocorrect: false,
            ),
            const SizedBox(height: 12),
            const Text('API key (optional)', style: TextStyle(fontWeight: FontWeight.w600)),
            const SizedBox(height: 8),
            TextField(
              controller: _apiKeyCtrl,
              decoration: const InputDecoration(
                hintText: 'x-api-key if required by server',
                border: OutlineInputBorder(),
              ),
              obscureText: true,
              autocorrect: false,
            ),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: () async {
                await ApiClient.setBaseUrl(_apiUrlCtrl.text);
                await ApiClient.setApiKey(
                  _apiKeyCtrl.text.trim().isEmpty ? null : _apiKeyCtrl.text,
                );
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Connection settings saved')),
                  );
                }
              },
              child: const Text('Save connection settings'),
            ),
            const Divider(height: 40),
            const Text('User session ID', style: TextStyle(fontWeight: FontWeight.w600)),
            const SizedBox(height: 8),
            TextField(
              controller: _userIdCtrl,
              decoration: const InputDecoration(border: OutlineInputBorder()),
            ),
            const SizedBox(height: 12),
            FilledButton(
              onPressed: () async {
                await userIdNotifier.setUserId(_userIdCtrl.text.trim());
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Saved')),
                  );
                }
              },
              child: const Text('Save user ID'),
            ),
          ],
        ),
      ),
    );
  }
}
