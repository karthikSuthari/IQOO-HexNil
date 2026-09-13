package com.example.iqoo_hexnil.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable

private val HexnilColorScheme = darkColorScheme(
    primary = HexnilMainAccent,
    secondary = HexnilAccentGlow,
    background = HexnilBackground,
    surface = HexnilCard,
    surfaceVariant = HexnilSecondaryCard,
    onPrimary = HexnilPrimaryText,
    onSecondary = HexnilPrimaryText,
    onBackground = HexnilPrimaryText,
    onSurface = HexnilPrimaryText,
    onSurfaceVariant = HexnilSecondaryText,
    outline = HexnilBorder,
    outlineVariant = HexnilBorderSubtle
)

@Composable
fun IQOOHEXNILTheme(
    content: @Composable () -> Unit
) {
    MaterialTheme(
        colorScheme = HexnilColorScheme,
        typography = HexnilTypography,
        content = content
    )
}