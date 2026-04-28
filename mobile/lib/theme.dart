import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppTheme {
  // ── CivicPulse brand colors (matching web dashboard) ──
  static const Color bg = Color(0xFF0A0E14);
  static const Color surface = Color(0xFF111923);
  static const Color surfaceLight = Color(0xFF1A2332);
  static const Color border = Color(0xFF1E3A3A);
  static const Color borderBright = Color(0xFF2DD4A8);
  static const Color accent = Color(0xFF2DD4A8);
  static const Color accentDim = Color(0xFF1A8A6E);
  static const Color textPrimary = Color(0xFFE0F2F0);
  static const Color textSecondary = Color(0xFF8AA8A0);
  static const Color textMuted = Color(0xFF5A7A72);

  // CSS severity colors
  static const Color stable = Color(0xFF2DD4A8);
  static const Color elevated = Color(0xFFF5C542);
  static const Color high = Color(0xFFF57C42);
  static const Color critical = Color(0xFFEF4444);

  static Color cssColor(double score) {
    if (score >= 76) return critical;
    if (score >= 56) return high;
    if (score >= 31) return elevated;
    return stable;
  }

  static String cssLabel(double score) {
    if (score >= 76) return 'Critical';
    if (score >= 56) return 'High';
    if (score >= 31) return 'Elevated';
    return 'Stable';
  }

  static ThemeData get darkTheme {
    return ThemeData(
      brightness: Brightness.dark,
      scaffoldBackgroundColor: bg,
      colorScheme: const ColorScheme.dark(
        primary: accent,
        secondary: accentDim,
        surface: surface,
        onPrimary: bg,
        onSurface: textPrimary,
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: surface,
        elevation: 0,
        centerTitle: true,
        titleTextStyle: GoogleFonts.spaceMono(
          fontSize: 18,
          fontWeight: FontWeight.w700,
          color: accent,
          letterSpacing: 1.5,
        ),
        iconTheme: const IconThemeData(color: accent),
      ),
      textTheme: TextTheme(
        headlineLarge: GoogleFonts.spaceMono(
          fontSize: 28,
          fontWeight: FontWeight.w700,
          color: textPrimary,
        ),
        headlineMedium: GoogleFonts.spaceMono(
          fontSize: 22,
          fontWeight: FontWeight.w600,
          color: textPrimary,
        ),
        titleLarge: GoogleFonts.spaceMono(
          fontSize: 16,
          fontWeight: FontWeight.w600,
          color: textPrimary,
        ),
        titleMedium: GoogleFonts.spaceMono(
          fontSize: 14,
          fontWeight: FontWeight.w500,
          color: textPrimary,
        ),
        bodyLarge: GoogleFonts.spaceMono(
          fontSize: 14,
          color: textSecondary,
        ),
        bodyMedium: GoogleFonts.spaceMono(
          fontSize: 12,
          color: textSecondary,
        ),
        labelLarge: GoogleFonts.spaceMono(
          fontSize: 14,
          fontWeight: FontWeight.w600,
          color: accent,
          letterSpacing: 1.2,
        ),
      ),
      cardTheme: CardThemeData(
        color: surface,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: const BorderSide(color: border, width: 1),
        ),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: accent,
          foregroundColor: bg,
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
          textStyle: GoogleFonts.spaceMono(
            fontWeight: FontWeight.w700,
            fontSize: 14,
            letterSpacing: 1,
          ),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: surfaceLight,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: border),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: border),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: accent, width: 2),
        ),
        labelStyle: GoogleFonts.spaceMono(color: textMuted, fontSize: 12),
        hintStyle: GoogleFonts.spaceMono(color: textMuted, fontSize: 12),
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: surface,
        selectedItemColor: accent,
        unselectedItemColor: textMuted,
        type: BottomNavigationBarType.fixed,
        elevation: 8,
      ),
      dividerColor: border,
    );
  }
}
