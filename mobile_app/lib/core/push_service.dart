import 'package:flutter_riverpod/flutter_riverpod.dart';

final pushInitProvider = Provider<void>((ref) {
  // Setup firebase messaging or similar push notification service here
  print("Push service initialized stub");
});
