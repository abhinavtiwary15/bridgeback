import 'package:bridgeback_mobile/core/api_client.dart';
import 'package:bridgeback_mobile/main.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUp(() async {
    SharedPreferences.setMockInitialValues({});
    await ApiClient.ensureInitialized();
  });

  testWidgets('BridgeBack app builds', (WidgetTester tester) async {
    await tester.pumpWidget(
      const ProviderScope(child: BridgeBackApp()),
    );
    await tester.pump();
    expect(find.text('BridgeBack'), findsWidgets);
  });
}
