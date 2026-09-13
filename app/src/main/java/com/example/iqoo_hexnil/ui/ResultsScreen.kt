package com.example.iqoo_hexnil.ui

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.iqoo_hexnil.data.ComparisonAnalysis
import com.example.iqoo_hexnil.data.VerdictType
import com.example.iqoo_hexnil.ui.components.EmptyState
import com.example.iqoo_hexnil.ui.components.EvidenceCoverageCard
import com.example.iqoo_hexnil.ui.components.MetricCard
import com.example.iqoo_hexnil.ui.components.SectionHeader
import com.example.iqoo_hexnil.ui.theme.HexnilAccentGlow
import com.example.iqoo_hexnil.ui.theme.HexnilAccentSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilBackground
import com.example.iqoo_hexnil.ui.theme.HexnilBorder
import com.example.iqoo_hexnil.ui.theme.HexnilCard
import com.example.iqoo_hexnil.ui.theme.HexnilError
import com.example.iqoo_hexnil.ui.theme.HexnilErrorSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilMainAccent
import com.example.iqoo_hexnil.ui.theme.HexnilPrimaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryCard
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSuccess
import com.example.iqoo_hexnil.ui.theme.HexnilSuccessSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilWarning

@Composable
fun ResultsScreen(
    analysis: ComparisonAnalysis,
    onNavigateToMetricDetail: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    val scrollState = rememberScrollState()
    var selectedFilter by remember { mutableStateOf<VerdictType?>(null) }

    val filteredMetrics = if (selectedFilter != null) {
        analysis.metricResults.filter { it.verdict == selectedFilter }
    } else {
        analysis.metricResults
    }

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(HexnilBackground)
            .padding(horizontal = 16.dp, vertical = 12.dp)
            .verticalScroll(scrollState),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        // Experiment Pair Header Context Card
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(12.dp))
                .border(1.dp, HexnilBorder, RoundedCornerShape(12.dp)),
            color = HexnilCard
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "V0 VS V1 COMPARISON MATRIX",
                        color = HexnilMainAccent,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 1.sp
                    )
                    Text(
                        text = analysis.comparisonId,
                        color = HexnilAccentGlow,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                }

                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = "Statistical Classifier Results",
                    color = HexnilPrimaryText,
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = "Paired t-test comparisons across 13 metrics. A positive delta alone does not constitute a regression: the hypothesis test and 5.0% threshold are authoritative.",
                    color = HexnilSecondaryText,
                    fontSize = 11.sp,
                    lineHeight = 15.sp
                )

                Spacer(modifier = Modifier.height(10.dp))

                // Lineage Metadata Row
                Surface(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(6.dp),
                    color = HexnilSecondaryCard,
                    border = BorderStroke(1.dp, HexnilBorder)
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 10.dp, vertical = 6.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(text = "V0: ${analysis.v0ExperimentId}", color = HexnilSecondaryText, fontSize = 10.sp, fontFamily = FontFamily.Monospace)
                        Text(text = "➔", color = HexnilSecondaryText, fontSize = 10.sp)
                        Text(text = "V1: ${analysis.v1ExperimentId}", color = HexnilAccentGlow, fontSize = 10.sp, fontFamily = FontFamily.Monospace)
                        Text(text = "· 3 runs paired", color = HexnilSecondaryText, fontSize = 10.sp)
                    }
                }
            }
        }

        // Authoritative Regression Banner
        Surface(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(8.dp),
            color = if (analysis.metricsRegressions == 0) HexnilSuccessSubtle else HexnilErrorSubtle,
            border = BorderStroke(1.dp, if (analysis.metricsRegressions == 0) HexnilSuccess.copy(alpha = 0.5f) else HexnilError.copy(alpha = 0.5f))
        ) {
            Column(modifier = Modifier.padding(12.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = if (analysis.metricsRegressions == 0) "✓ " else "⚠ ",
                        color = if (analysis.metricsRegressions == 0) HexnilSuccess else HexnilError,
                        fontWeight = FontWeight.Black,
                        fontSize = 14.sp
                    )
                    Text(
                        text = if (analysis.metricsRegressions == 0) "No statistically supported regressions detected." else "${analysis.metricsRegressions} statistically supported regression(s) detected.",
                        color = if (analysis.metricsRegressions == 0) HexnilSuccess else HexnilError,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold
                    )
                }
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = "INCONCLUSIVE ≠ REGRESSION · UNSUPPORTED ≠ REGRESSION · INVALID ≠ REGRESSION",
                    color = HexnilSecondaryText,
                    fontSize = 9.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 0.5.sp
                )
            }
        }

        // Filter Verdict Chips Row
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(5.dp)
        ) {
            FilterVerdictChip(
                label = "ALL (${analysis.metricsAnalyzed})",
                isSelected = selectedFilter == null,
                color = HexnilMainAccent,
                onClick = { selectedFilter = null },
                modifier = Modifier.weight(1f)
            )
            FilterVerdictChip(
                label = "UNCHANGED (${analysis.metricsUnchanged})",
                isSelected = selectedFilter == VerdictType.UNCHANGED,
                color = HexnilSuccess,
                onClick = { selectedFilter = VerdictType.UNCHANGED },
                modifier = Modifier.weight(1.3f)
            )
            FilterVerdictChip(
                label = "INCONCL. (${analysis.metricsInconclusive})",
                isSelected = selectedFilter == VerdictType.INCONCLUSIVE,
                color = HexnilWarning,
                onClick = { selectedFilter = VerdictType.INCONCLUSIVE },
                modifier = Modifier.weight(1.2f)
            )
            FilterVerdictChip(
                label = "REG. (${analysis.metricsRegressions})",
                isSelected = selectedFilter == VerdictType.REGRESSION,
                color = HexnilError,
                onClick = { selectedFilter = VerdictType.REGRESSION },
                modifier = Modifier.weight(0.9f)
            )
        }

        // Section Title
        SectionHeader(
            category = "METRIC-BY-METRIC STATISTICAL TABLE",
            subtitle = "Tap any metric card to inspect raw run observations, 95% CI, p-value, and threshold reasoning."
        )

        // Empty state when filtering by Regressions
        if (filteredMetrics.isEmpty()) {
            EmptyState(
                title = "Zero Regressions Detected",
                message = "The statistical engine authoritatively detected 0 regressions in this comparison. All shifts remain within acceptable engineering thresholds.",
                actionText = "Show All Metrics",
                onActionClick = { selectedFilter = null }
            )
        } else {
            // List of Metric Cards
            filteredMetrics.forEach { metric ->
                MetricCard(
                    metric = metric,
                    onClick = { onNavigateToMetricDetail(metric.key) }
                )
            }
        }

        Spacer(modifier = Modifier.height(16.dp))
    }
}

@Composable
private fun FilterVerdictChip(
    label: String,
    isSelected: Boolean,
    color: Color,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val bgColor = if (isSelected) HexnilAccentSubtle else HexnilSecondaryCard
    val borderColor = if (isSelected) color else HexnilBorder

    Surface(
        modifier = modifier.clickable { onClick() },
        shape = RoundedCornerShape(6.dp),
        color = bgColor,
        border = BorderStroke(1.dp, borderColor)
    ) {
        Text(
            text = label,
            color = if (isSelected) color else HexnilSecondaryText,
            fontSize = 9.sp,
            fontWeight = if (isSelected) FontWeight.Bold else FontWeight.SemiBold,
            modifier = Modifier.padding(vertical = 8.dp, horizontal = 2.dp),
            maxLines = 1
        )
    }
}
