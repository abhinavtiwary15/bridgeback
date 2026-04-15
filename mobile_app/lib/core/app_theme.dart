import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

// ── BridgeBack Design Tokens ──────────────────────────────────────────────────

class AppColors {
  AppColors._();

  // Primary palette — Forest Green
  static const primary = Color(0xFF1B4332);
  static const primaryLight = Color(0xFF40916C);
  static const primaryMid = Color(0xFF52B788);
  static const accent = Color(0xFF74C69D);
  static const accentSoft = Color(0xFFD8F3DC);

  // Backgrounds
  static const background = Color(0xFFF6FAF7);
  static const surface = Color(0xFFFFFFFF);
  static const surfaceElevated = Color(0xFFF0F7F2);

  // Text
  static const textPrimary = Color(0xFF1A2523);
  static const textSecondary = Color(0xFF5A7069);
  static const textHint = Color(0xFF9DBDAB);

  // Status
  static const statusPending = Color(0xFFE9C46A);
  static const statusPendingBg = Color(0xFFFFF8E1);
  static const statusDone = Color(0xFF52B788);
  static const statusDoneBg = Color(0xFFE8F5E9);

  // Chat bubbles
  static const userBubble = Color(0xFF1B4332);
  static const aiBubble = Color(0xFFFFFFFF);

  // Floating nav
  static const navBackground = Color(0xFF1B4332);
  static const navSelected = Color(0xFF74C69D);
  static const navUnselected = Color(0xFF52B788);

  // Shadows
  static List<BoxShadow> get cardShadow => [
        BoxShadow(
          color: const Color(0xFF1B4332).withValues(alpha: 0.08),
          blurRadius: 20,
          offset: const Offset(0, 6),
        ),
      ];

  static List<BoxShadow> get floatShadow => [
        BoxShadow(
          color: const Color(0xFF1B4332).withValues(alpha: 0.25),
          blurRadius: 30,
          offset: const Offset(0, 10),
        ),
      ];
}

// ── Theme Builder ─────────────────────────────────────────────────────────────

ThemeData buildAppTheme() {
  return ThemeData(
    useMaterial3: true,
    colorScheme: ColorScheme.fromSeed(
      seedColor: AppColors.primary,
      primary: AppColors.primary,
      secondary: AppColors.primaryLight,
      tertiary: AppColors.accent,
      surface: AppColors.surface,
      onPrimary: Colors.white,
      onSecondary: Colors.white,
    ),
    scaffoldBackgroundColor: AppColors.background,

    // Typography
    fontFamily: 'DMSans',
    textTheme: const TextTheme(
      displayLarge: TextStyle(
        fontSize: 32,
        fontWeight: FontWeight.w700,
        color: AppColors.textPrimary,
        letterSpacing: -0.5,
      ),
      titleLarge: TextStyle(
        fontSize: 20,
        fontWeight: FontWeight.w700,
        color: AppColors.textPrimary,
        letterSpacing: -0.3,
      ),
      titleMedium: TextStyle(
        fontSize: 16,
        fontWeight: FontWeight.w600,
        color: AppColors.textPrimary,
      ),
      bodyLarge: TextStyle(
        fontSize: 15,
        fontWeight: FontWeight.w400,
        color: AppColors.textPrimary,
        height: 1.5,
      ),
      bodyMedium: TextStyle(
        fontSize: 14,
        fontWeight: FontWeight.w400,
        color: AppColors.textSecondary,
        height: 1.5,
      ),
      labelMedium: TextStyle(
        fontSize: 12,
        fontWeight: FontWeight.w500,
        color: AppColors.textSecondary,
        letterSpacing: 0.3,
      ),
    ),

    // AppBar
    appBarTheme: AppBarTheme(
      backgroundColor: AppColors.background,
      foregroundColor: AppColors.textPrimary,
      elevation: 0,
      scrolledUnderElevation: 0,
      systemOverlayStyle: SystemUiOverlayStyle.dark,
      titleTextStyle: const TextStyle(
        fontFamily: 'DMSans',
        fontSize: 20,
        fontWeight: FontWeight.w700,
        color: AppColors.textPrimary,
        letterSpacing: -0.3,
      ),
      iconTheme: const IconThemeData(color: AppColors.textPrimary),
    ),

    // Cards
    cardTheme: const CardThemeData(
      color: AppColors.surface,
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.all(Radius.circular(20)),
      ),
      margin: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
    ),

    // Elevated Button
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
        elevation: 0,
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(50)),
        textStyle: const TextStyle(
          fontFamily: 'DMSans',
          fontSize: 14,
          fontWeight: FontWeight.w600,
          letterSpacing: 0.2,
        ),
      ),
    ),

    // Input fields
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: AppColors.surfaceElevated,
      hintStyle: const TextStyle(
        color: AppColors.textHint,
        fontSize: 15,
        fontWeight: FontWeight.w400,
      ),
      contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(50),
        borderSide: BorderSide.none,
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(50),
        borderSide: BorderSide.none,
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(50),
        borderSide: const BorderSide(color: AppColors.primaryLight, width: 1.5),
      ),
    ),

    // Icon
    iconTheme: const IconThemeData(color: AppColors.textPrimary, size: 22),

    // Divider
    dividerTheme: const DividerThemeData(
      color: Color(0xFFEAF2EC),
      thickness: 1,
      space: 1,
    ),
  );
}
