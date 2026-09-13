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
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryCard
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryText
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
            .padding(horizontal = 16.dp, vertical = 12.dp)
            .verticalScroll(scrollState),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        // App Version Card
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(12.dp))
                .border(1.dp, HexnilBorder, RoundedCornerShape(12.dp)),
            color = HexnilCard
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text(
                    text = "SYSTEM ARCHITECTURE & METHODOLOGY",
                    color = HexnilMainAccent,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp
                )
                Spacer(modifier = Modifier.height(6.dp))
                Text(
                    text = "Hexnil Release Intelligence",
                    color = HexnilPrimaryText,
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = "Automated release-validation intelligence system for the iQOO Hyderabad Edition Hackathon.",
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
                .clip(RoundedCornerShape(12.dp))
                .border(1.dp, HexnilBorder, RoundedCornerShape(12.dp)),
            color = HexnilCard
        ) {
            Column(modifier = Modifier.padding(14.dp)) {
                SettingsInfoRow("Hexnil Companion App", "v1.1 (Build 2)")
                SettingsInfoRow("Statistical Engine Phase", "Phase 6 (Analysis v1.0.0)")
                SettingsInfoRow("Engineering Threshold", "5.0% meaningful shift delta")
                SettingsInfoRow("Telemetry Collector API", "Phase 2 Capability Matrix")
                SettingsInfoRow("Workload Runtime", "Phase 3 Deterministic Engine")
                SettingsInfoRow("Multiple Comparison Policy", "Pairwise Significance (alpha = 0.05)")
            }
        }

        // Core Data Honesty Rules Card
        SectionHeader(
            category = "DATA HONESTY & EVIDENCE RULES",
            subtitle = "Guiding principles governing automated statistical conclusions."
        )

        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(12.dp))
                .border(1.dp, HexnilBorder, RoundedCornerShape(12.dp)),
            color = HexnilCard
        ) {
            Column(modifier = Modifier.padding(14.dp)) {
                RuleItem("1. INCONCLUSIVE ≠ REGRESSION", "High variance crossing zero or sample size n < 3 is inconclusive, not an engineering regression.")
                Spacer(modifier = Modifier.height(8.dp))
                RuleItem("2. UNSUPPORTED ≠ ZERO", "Missing hardware sensor capabilities are recorded as UNSUPPORTED rather than zero.")
                Spacer(modifier = Modifier.height(8.dp))
                RuleItem("3. THRESHOLD MATTERS", "Statistical significance (p < 0.05) does not constitute a regression if magnitude is below the 5.0% engineering threshold.")
                Spacer(modifier = Modifier.height(8.dp))
                RuleItem("4. AUDITABLE PROVENANCE", "Every observation maps to an immutable experiment run, APK SHA-256 hash, and storage directory.")
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
        Text(text = label, color = HexnilSecondaryText, fontSize = 12.sp)
        Text(
            text = value,
            color = HexnilPrimaryText,
            fontSize = 12.sp,
            fontWeight = FontWeight.Medium,
            fontFamily = FontFamily.Monospace
        )
    }
}

@Composable
private fun RuleItem(title: String, desc: String) {
    Surface(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(8.dp),
        color = HexnilSecondaryCard,
        border = BorderStroke(1.dp, HexnilBorder)
    ) {
        Column(modifier = Modifier.padding(10.dp)) {
            Text(text = title, color = HexnilAccentGlow, fontSize = 11.sp, fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(2.dp))
            Text(text = desc, color = HexnilSecondaryText, fontSize = 11.sp, lineHeight = 15.sp)
        }
    }
}
