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
import com.example.iqoo_hexnil.data.ComparisonAnalysis
import com.example.iqoo_hexnil.ui.components.ComparisonCard
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
fun V0V1ComparisonScreen(
    analysis: ComparisonAnalysis,
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
        // Paired Experiment Lock Header Card
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(HexnilRadius.hero))
                .border(1.dp, HexnilBorder, RoundedCornerShape(HexnilRadius.hero)),
            color = HexnilCard
        ) {
            Column(modifier = Modifier.padding(HexnilSpacing.md)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "MATCHED DIFFERENTIAL EXPERIMENT",
                        color = HexnilMainAccent,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 1.sp
                    )
                    Text(
                        text = analysis.comparisonId,
                        color = HexnilAccentGlow,
                        fontSize = 11.sp,
                        fontFamily = FontFamily.Monospace,
                        fontWeight = FontWeight.Bold
                    )
                }

                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = "SAME DEVICE + SAME WORKLOAD + V0 vs V1",
                    color = HexnilPrimaryText,
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = "All runs execute under locked physical thermal boundaries, battery charge state, and identical workload seeds to isolate true software deltas.",
                    color = HexnilSecondaryText,
                    fontSize = 11.sp,
                    lineHeight = 15.sp
                )

                Spacer(modifier = Modifier.height(10.dp))

                // Build Fingerprint & Hash Matching Box (No nested border)
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(HexnilSecondaryCard, RoundedCornerShape(HexnilRadius.metadata))
                        .padding(10.dp)
                ) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text(text = "Target Hardware", color = HexnilSecondaryText, fontSize = 11.sp)
                            Text(text = analysis.deviceModel, color = HexnilPrimaryText, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                        }
                        Spacer(modifier = Modifier.height(4.dp))
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text(text = "V0 Experiment", color = HexnilSecondaryText, fontSize = 11.sp)
                            Text(text = analysis.v0ExperimentId, color = HexnilAccentGlow, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                        }
                        Spacer(modifier = Modifier.height(4.dp))
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text(text = "V1 Experiment", color = HexnilSecondaryText, fontSize = 11.sp)
                            Text(text = analysis.v1ExperimentId, color = HexnilAccentGlow, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                        }
                        Spacer(modifier = Modifier.height(4.dp))
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text(text = "Engineering Threshold", color = HexnilSecondaryText, fontSize = 11.sp)
                            Text(text = "5.0% meaningful change", color = HexnilSuccess, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                        }
                    }
            }
        }

        // Section Title
        SectionHeader(
            category = "MATCHED RUN PAIRINGS",
            subtitle = "Direct side-by-side run observations across deterministic workloads."
        )

        // Comparison Cards
        analysis.metricResults.forEach { metric ->
            ComparisonCard(
                metric = metric,
                v0ExpId = analysis.v0ExperimentId,
                v1ExpId = analysis.v1ExperimentId
            )
        }

        Spacer(modifier = Modifier.height(16.dp))
    }
}
