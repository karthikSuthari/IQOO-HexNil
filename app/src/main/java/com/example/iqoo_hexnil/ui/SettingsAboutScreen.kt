package com.example.iqoo_hexnil.ui

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.iqoo_hexnil.ui.components.SectionHeader
import com.example.iqoo_hexnil.ui.theme.HexnilAccentGlow
import com.example.iqoo_hexnil.ui.theme.HexnilBackground
import com.example.iqoo_hexnil.ui.theme.HexnilBorder
import com.example.iqoo_hexnil.ui.theme.HexnilCard
import com.example.iqoo_hexnil.ui.theme.HexnilMainAccent
import com.example.iqoo_hexnil.ui.theme.HexnilPrimaryText
import com.example.iqoo_hexnil.ui.theme.HexnilRadius
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryCard
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSpacing
import com.example.iqoo_hexnil.ui.theme.HexnilSuccess

@Composable
fun SettingsAboutScreen(
    modifier: Modifier = Modifier
) {
    val scrollState = rememberScrollState()

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(HexnilBackground)
            .padding(horizontal = HexnilSpacing.md, vertical = HexnilSpacing.sm)
            .verticalScroll(scrollState),
        verticalArrangement = Arrangement.spacedBy(HexnilSpacing.sm)
    ) {
        // Methodology Hero Card
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(HexnilRadius.hero))
                .border(1.dp, HexnilBorder, RoundedCornerShape(HexnilRadius.hero)),
            color = HexnilCard
        ) {
            Column(modifier = Modifier.padding(HexnilSpacing.md)) {
                Text(
                    text = "HEXNIL METHODOLOGY & INTEGRITY",
                    color = HexnilMainAccent,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp
                )
                Spacer(modifier = Modifier.height(6.dp))
                Text(
                    text = "Release Validation Intelligence",
                    color = HexnilPrimaryText,
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = "Hexnil enforces statistical evidence, capability-aware telemetry, and immutable auditability for Android software update validation.",
                    color = HexnilSecondaryText,
                    fontSize = 12.sp,
                    lineHeight = 16.sp
                )
            }
        }

        // Engine Specification Matrix
        SectionHeader(
            category = "ENGINE SPECIFICATION VERSIONS",
            subtitle = "Active release validation algorithms and threshold models."
        )

        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(HexnilRadius.card))
                .border(1.dp, HexnilBorder, RoundedCornerShape(HexnilRadius.card)),
            color = HexnilCard
        ) {
            Column(modifier = Modifier.padding(HexnilSpacing.md)) {
                SettingsInfoRow("Hexnil Companion App", "v1.1 (Build 2)")
                SettingsInfoRow("Statistical Engine Phase", "Phase 6 (Analysis v1.0.0)")
                SettingsInfoRow("Engineering Threshold", "5.0% meaningful shift delta")
                SettingsInfoRow("Telemetry Collector API", "Phase 2 Capability Matrix")
                SettingsInfoRow("Workload Runtime", "Phase 3 Deterministic Engine")
                SettingsInfoRow("Multiple Comparison Policy", "Pairwise Student's t-test (α = 0.05)")
                SettingsInfoRow("Immutable Random Seed", "42 (Deterministic Locked)")
            }
        }

        // Core Data Honesty Rules Card (Clean list without nested border spam)
        SectionHeader(
            category = "DATA HONESTY & EVIDENCE PRINCIPLES",
            subtitle = "Non-negotiable mathematical guardrails governing all verdicts."
        )

        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(HexnilRadius.card))
                .border(1.dp, HexnilBorder, RoundedCornerShape(HexnilRadius.card)),
            color = HexnilCard
        ) {
            Column(modifier = Modifier.padding(HexnilSpacing.md), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                RuleItem("1. INCONCLUSIVE ≠ REGRESSION", "High variance crossing zero or sample size n < 3 is classified as INCONCLUSIVE, never as an engineering regression.")
                RuleItem("2. UNSUPPORTED ≠ ZERO", "Missing hardware sensor capabilities are recorded as UNSUPPORTED. Hexnil never fabricates sensor values.")
                RuleItem("3. THRESHOLD MATTERS", "Statistical significance (p < 0.05) does not constitute a regression if the delta is below the 5.0% engineering threshold.")
                RuleItem("4. AUDITABLE PROVENANCE", "Every observation traces back to an immutable experiment run, APK SHA-256 hash, and storage directory.")
            }
        }

        Spacer(modifier = Modifier.height(16.dp))
    }
}

@Composable
private fun SettingsInfoRow(label: String, value: String) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(text = label, color = HexnilSecondaryText, fontSize = 11.sp)
        Text(
            text = value,
            color = HexnilPrimaryText,
            fontSize = 11.sp,
            fontWeight = FontWeight.Medium,
            fontFamily = FontFamily.Monospace
        )
    }
}

@Composable
private fun RuleItem(title: String, desc: String) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(HexnilSecondaryCard, RoundedCornerShape(HexnilRadius.metadata))
            .padding(horizontal = 12.dp, vertical = 8.dp)
    ) {
        Text(text = title, color = HexnilAccentGlow, fontSize = 11.sp, fontWeight = FontWeight.Bold)
        Spacer(modifier = Modifier.height(2.dp))
        Text(text = desc, color = HexnilSecondaryText, fontSize = 11.sp, lineHeight = 15.sp)
    }
}
