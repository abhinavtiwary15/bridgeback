import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

final userIdProvider = NotifierProvider<UserIdController, String>(() {
  return UserIdController();
});

class UserIdController extends Notifier<String> {
  @override
  String build() {
    // Load initial state asynchronously after build
    load();
    return 'default-mobile';
  }

  Future<void> load() async {
    final prefs = await SharedPreferences.getInstance();
    final value = prefs.getString('bridgeback_user_id');
    if (value != null && value.isNotEmpty) {
      state = value;
      return;
    }
    await prefs.setString('bridgeback_user_id', state);
  }

  Future<void> setUserId(String value) async {
    state = value;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('bridgeback_user_id', value);
  }
}
