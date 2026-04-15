import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/api_client.dart';
import 'core/app_router.dart';
import 'core/app_theme.dart';
import 'core/push_service.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await ApiClient.ensureInitialized();
  runApp(const ProviderScope(child: BridgeBackApp()));
}

class BridgeBackApp extends ConsumerWidget {
  const BridgeBackApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    ref.watch(pushInitProvider);
    final router = ref.watch(appRouterProvider);
    return MaterialApp.router(
      title: 'BridgeBack',
      theme: buildAppTheme(),
      routerConfig: router,
      debugShowCheckedModeBanner: false,
    );
  }
}
