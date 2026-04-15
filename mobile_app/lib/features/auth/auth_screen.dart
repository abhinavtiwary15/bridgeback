import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:dio/dio.dart';
import '../../core/api_client.dart';
import 'package:go_router/go_router.dart';

class AuthScreen extends StatefulWidget {
  const AuthScreen({Key? key}) : super(key: key);
  @override
  _AuthScreenState createState() => _AuthScreenState();
}

class _AuthScreenState extends State<AuthScreen> {
  bool isLogin = true;
  final userCtrl = TextEditingController();
  final passCtrl = TextEditingController();
  final telegramChatIdCtrl = TextEditingController();
  final apiUrlCtrl = TextEditingController();
  final apiKeyCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    _loadPrefs();
  }

  Future<void> _loadPrefs() async {
    final prefs = await SharedPreferences.getInstance();
    final url = prefs.getString('bridgeback_api_base_url') ??
        const String.fromEnvironment('API_URL', defaultValue: 'https://abhinavtiwary-bridgeback.hf.space');
    final key = prefs.getString('bridgeback_api_key') ??
        const String.fromEnvironment('API_AUTH_TOKEN', defaultValue: '');
    if (!mounted) return;
    setState(() {
      apiUrlCtrl.text = url;
      apiKeyCtrl.text = key;
    });
  }

  Future<void> _submit() async {
    final base = apiUrlCtrl.text.trim();
    if (base.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Enter your BridgeBack server URL (from your host or team).'),
        ),
      );
      return;
    }

    await ApiClient.setBaseUrl(base);
    await ApiClient.setApiKey(apiKeyCtrl.text.trim().isEmpty ? null : apiKeyCtrl.text);

    try {
      if (isLogin) {
        var formData = FormData.fromMap({
          'username': userCtrl.text,
          'password': passCtrl.text,
        });
        var res = await ApiClient.instance.post('/auth/token', data: formData);
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString('access_token', res.data['access_token']);
        await prefs.setString('user_id', userCtrl.text);
        if (mounted) context.go('/');
      } else {
        await ApiClient.instance.post('/auth/register', data: {
          'username': userCtrl.text,
          'password': passCtrl.text,
          'telegram_chat_id': telegramChatIdCtrl.text,
        });
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Registered! Please login.')),
          );
          setState(() => isLogin = true);
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e')),
        );
      }
    }
  }

  @override
  void dispose() {
    userCtrl.dispose();
    passCtrl.dispose();
    telegramChatIdCtrl.dispose();
    apiUrlCtrl.dispose();
    apiKeyCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('BridgeBack')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const SizedBox(height: 24),
            TextField(
              controller: userCtrl,
              decoration: const InputDecoration(
                labelText: 'Username',
                prefixIcon: Icon(Icons.person_outline),
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: passCtrl,
              decoration: const InputDecoration(
                labelText: 'Password',
                prefixIcon: Icon(Icons.lock_outline),
                border: OutlineInputBorder(),
              ),
              obscureText: true,
            ),
            if (!isLogin) ...[
              const SizedBox(height: 16),
              TextField(
                controller: telegramChatIdCtrl,
                decoration: const InputDecoration(
                  labelText: 'Telegram Chat ID',
                  prefixIcon: Icon(Icons.send_outlined),
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 8),
              const Text(
                'Find your ID by messaging @userinfobot on Telegram.',
                style: TextStyle(fontSize: 12, color: Colors.grey),
              ),
            ],
            const SizedBox(height: 12),
            Theme(
              data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
              child: ExpansionTile(
                title: const Text(
                  'Advanced Settings',
                  style: TextStyle(fontSize: 14, color: Colors.blueGrey),
                ),
                children: [
                  TextField(
                    controller: apiUrlCtrl,
                    decoration: const InputDecoration(
                      labelText: 'Server URL',
                      hintText: 'https://your-api.example.com',
                      helperText: 'Dev: http://YOUR_PC_IP:8000',
                    ),
                    keyboardType: TextInputType.url,
                    autocorrect: false,
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: apiKeyCtrl,
                    decoration: const InputDecoration(
                      labelText: 'API key (optional)',
                      hintText: 'Only if your server uses x-api-key',
                    ),
                    obscureText: true,
                    autocorrect: false,
                  ),
                  const SizedBox(height: 16),
                ],
              ),
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: _submit,
              child: Text(isLogin ? 'Login' : 'Register'),
            ),
            TextButton(
              onPressed: () => setState(() => isLogin = !isLogin),
              child: Text(
                isLogin ? 'Need an account? Register' : 'Have an account? Login',
              ),
            ),
          ],
        ),
      ),
    );
  }
}
