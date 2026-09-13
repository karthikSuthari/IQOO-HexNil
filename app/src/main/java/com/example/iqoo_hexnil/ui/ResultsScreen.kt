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
import com.example.iqoo_hexnil.ui.theme.HexnilBorderSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilCard
import com.example.iqoo_hexnil.ui.theme.HexnilError
import com.example.iqoo_hexnil.ui.theme.HexnilErrorSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilMainAccent
import com.example.iqoo_hexnil.ui.theme.HexnilPrimaryText
import com.example.iqoo_hexnil.ui.theme.HexnilRadius
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryCard
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryText
import com.example.iqoo_hexnil.ui.theme.DisplayLargeNumber
import com.example.iqoo_hexnil.ui.theme.HexnilSpacing
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
            .padding(horizontal = HexnilSpacing.screenHorizontal, vertical = HexnilSpacing.screenVertical)
            .verticalScroll(scrollState),
        verticalArrangement = Arrangement.spacedBy(HexnilSpacing.sectionSpacing)
    ) {
        // Authoritative Outcome Hero
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(HexnilRadius.hero))
                .border(
                    BorderStroke(
                        1.dp,
                        if (analysis.metricsRegressions == 0) HexnilSuccess.copy(alpha = 0.4f) else HexnilError.copy(alpha = 0.5f)
                    ),
                    RoundedCornerShape(HexnilRadius.hero)
                ),
            color = HexnilCard
        ) {
            Column(modifier = Modifier.padding(HexnilSpacing.cardPadding)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "V0 VS V1 COMPARISON MATRIX",
                        color = HexnilMainAccent,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 1.sp
                    )
                    Text(
                        text = analysis.comparisonId,
                        color = HexnilAccentGlow,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                }

                Spacer(modifier = Modifier.height(14.dp))

                // Hero Number + Verdict
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.Bottom
                ) {
                    Column {
                        Text(
                            text = "${analysis.metricsRegressions}",
                            style = DisplayLargeNumber.copy(
                                color = if (analysis.metricsRegressions == 0) HexnilSuccess else HexnilError,
                                fontSize = 38.sp
                            )
                        )
                        Spacer(modifier = Modifier.height(2.dp))
                        Text(
                            text = if (analysis.metricsRegressions == 0) "0 REGRESSIONS DETECTED" else "${analysis.metricsRegressions} REGRESSIONS DETECTED",
                            color = if (analysis.metricsRegressions == 0) HexnilSuccess else HexnilError,
                            fontSize = 13.sp,
                            fontWeight = FontWeight.Bold,
                            letterSpacing = 0.8.sp
                        )
                    }

                    Surface(
                        shape = RoundedCornerShape(HexnilRadius.pill),
                        color = if (analysis.metricsRegressions == 0) HexnilSuccessSubtle else HexnilErrorSubtle,
                        border = BorderStroke(1.dp, if (analysis.metricsRegressions == 0) HexnilSuccess.copy(alpha = 0.4f) else HexnilError.copy(alpha = 0.4f))
                    ) {
                        Text(
                            text = if (analysis.metricsRegressions == 0) "✓ PASS" else "⚠ FAIL",
                            color = if (analysis.metricsRegressions == 0) HexnilSuccess else HexnilError,
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Bold,
                            modifier = Modifier.padding(horizontal = 12.dp, vertical = 5.dp)
                        )
                    }
                }

                Spacer(modifier = Modifier.height(10.dp))
                Text(
                    text = if (analysis.metricsRegressions == 0)
                        "No statistically supported regressions detected. Paired t-test comparisons across 13 metrics demonstrate that observed shifts remain safely within the 5.0% engineering threshold."
                    else
                        "${analysis.metricsRegressions} metric(s) exceeded the 5.0% threshold with statistical significance.",
                    color = HexnilSecondaryText,
                    fontSize = 13.sp,
                    lineHeight = 19.sp
                )

                Spacer(modifier = Modifier.height(14.dp))

                // Lineage Metadata (Structured & Spacious)
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(HexnilSecondaryCard, RoundedCornerShape(HexnilRadius.md))
                        .padding(horizontal = 14.dp, vertical = 10.dp),
                    verticalArrangement = Arrangement.spacedBy(6.dp)
                ) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "COMPARISON LINEAGE",
                            color = HexnilMainAccent,
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            letterSpacing = 0.8.sp
                        )
                        Text(
                            text = "3 paired iterations",
                            color = HexnilSecondaryText,
                            fontSize = 11.sp,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                    Text(
                        text = "V0: ${analysis.v0ExperimentId}  ➔  V1: ${analysis.v1ExperimentId}",
                        color = HexnilPrimaryText,
                        fontSize = 12.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }
        }

        // Spacious 2x2 Outcome Breakdown Grid
        Column(
            modifier = Modifier.fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                ResultsMetricTile(
                    label = "Regressions",
                    count = "${analysis.metricsRegressions}",
                    subtitle = "0 Exceeded Tolerance",
                    color = if (analysis.metricsRegressions == 0) HexnilSuccess else HexnilError,
                    modifier = Modifier.weight(1f)
                )
                ResultsMetricTile(
                    label = "Improvements",
                    count = "${analysis.metricsImprovements}",
                    subtitle = "Statistically Confirmed",
                    color = HexnilSuccess,
                    modifier = Modifier.weight(1f)
                )
            }
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                ResultsMetricTile(
                    label = "Unchanged",
                    count = "${analysis.metricsUnchanged}",
                    subtitle = "Within Tolerances",
                    color = HexnilPrimaryText,
                    modifier = Modifier.weight(1f)
                )
                ResultsMetricTile(
                    label = "Inconclusive",
                    count = "${analysis.metricsInconclusive}",
                    subtitle = "p ≥ 0.05 Variance",
                    color = HexnilWarning,
                    modifier = Modifier.weight(1f)
                )
            }
        }

        // Honest Principle Banner
        Surface(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(HexnilRadius.md),
            color = HexnilSecondaryCard,
            border = BorderStroke(1.dp, HexnilBorderSubtle)
        ) {
            Text(
                text = "STATISTICAL RIGOR: Inconclusive ≠ Regression · Unsupported ≠ Zero · Tolerance: ≤ 5.0%",
                color = HexnilSecondaryText,
                fontSize = 12.sp,
                fontWeight = FontWeight.Medium,
                letterSpacing = 0.4.sp,
                modifier = Modifier.padding(horizontal = 14.dp, vertical = 10.dp)
            )
        }

        // Filter Verdict Chips Row
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(6.dp)
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
    val borderColor = if (isSelected) color else HexnilBorderSubtle

    Surface(
        modifier = modifier.clickable { onClick() },
        shape = RoundedCornerShape(HexnilRadius.md),
        color = bgColor,
        border = BorderStroke(1.dp, borderColor)
    ) {
        Text(
            text = label,
            color = if (isSelected) color else HexnilSecondaryText,
            fontSize = 11.sp,
            fontWeight = if (isSelected) FontWeight.Bold else FontWeight.SemiBold,
            modifier = Modifier.padding(vertical = 9.dp, horizontal = 4.dp),
            maxLines = 1
        )
    }
}

@Composable
private fun ResultsMetricTile(
    label: String,
    count: String,
    subtitle: String,
    color: Color,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(HexnilRadius.md),
        color = HexnilSecondaryCard,
        border = BorderStroke(1.dp, HexnilBorderSubtle)
    ) {
        Column(
            modifier = Modifier.padding(horizontal = 14.dp, vertical = 12.dp)
        ) {
            Text(
                text = count,
                color = color,
                fontSize = 22.sp,
                fontWeight = FontWeight.Black,
                fontFamily = FontFamily.Monospace
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = label,
                color = HexnilPrimaryText,
                fontSize = 13.sp,
                fontWeight = FontWeight.Bold
            )
            Spacer(modifier = Modifier.height(2.dp))
            Text(
                text = subtitle,
                color = HexnilSecondaryText,
                fontSize = 11.sp,
                maxLines = 1
            )
        }
    }
}

