package com.example.iqoo_hexnil.ui

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
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
import com.example.iqoo_hexnil.data.HexnilRepository
import com.example.iqoo_hexnil.data.IssueCategory
import com.example.iqoo_hexnil.data.VerdictType
import com.example.iqoo_hexnil.ui.components.ExecutiveVerdictCard
import com.example.iqoo_hexnil.ui.components.IssueClassificationCard
import com.example.iqoo_hexnil.ui.components.MetricCard
import com.example.iqoo_hexnil.ui.components.PredictionOutcomeCard
import com.example.iqoo_hexnil.ui.components.SectionHeader
import com.example.iqoo_hexnil.ui.theme.HexnilAccentGlow
import com.example.iqoo_hexnil.ui.theme.HexnilAccentSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilBackground
import com.example.iqoo_hexnil.ui.theme.HexnilBorder
import com.example.iqoo_hexnil.ui.theme.HexnilBorderSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilCard
import com.example.iqoo_hexnil.ui.theme.HexnilCyan
import com.example.iqoo_hexnil.ui.theme.HexnilError
import com.example.iqoo_hexnil.ui.theme.HexnilFixed
import com.example.iqoo_hexnil.ui.theme.HexnilMainAccent
import com.example.iqoo_hexnil.ui.theme.HexnilPreExisting
import com.example.iqoo_hexnil.ui.theme.HexnilPrimaryText
import com.example.iqoo_hexnil.ui.theme.HexnilRadius
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryCard
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSpacing

@Composable
fun ResultsScreen(
    analysis: ComparisonAnalysis,
    onNavigateToMetricDetail: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    val scrollState = rememberScrollState()
    val filterScrollState = rememberScrollState()
    val report = remember { HexnilRepository.getFinalEvidenceReport() }
    val issueReport = remember { HexnilRepository.getIssueReport() }
    val predictionSummary = remember { HexnilRepository.getPredictionEvaluationSummary() }

    var selectedCategoryFilter by remember { mutableStateOf<IssueCategory?>(null) }

    val filteredIssues = if (selectedCategoryFilter != null) {
        issueReport.classifications.filter { it.category == selectedCategoryFilter }
    } else {
        issueReport.classifications
    }

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(HexnilBackground)
            .padding(horizontal = HexnilSpacing.screenHorizontal, vertical = HexnilSpacing.screenVertical)
            .verticalScroll(scrollState),
        verticalArrangement = Arrangement.spacedBy(HexnilSpacing.sectionSpacing)
    ) {
        // 1. Master Executive Verdict Card
        ExecutiveVerdictCard(
            verdict = report.executiveVerdict,
            evidenceCoverage = report.evidenceCoverage,
            regressionsCount = issueReport.newRegressionsCount,
            improvementsCount = issueReport.improvementsCount,
            persistedCount = issueReport.persistedCount,
            unchangedCount = issueReport.unchangedCount,
            inconclusiveCount = issueReport.inconclusiveCount
        )

        // 2. Filter Bar for Issue Classifications
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .horizontalScroll(filterScrollState),
            horizontalArrangement = Arrangement.spacedBy(6.dp)
        ) {
            CategoryFilterPill(
                label = "ALL (${issueReport.totalClassified})",
                isSelected = selectedCategoryFilter == null,
                onClick = { selectedCategoryFilter = null }
            )
            CategoryFilterPill(
                label = "NEW REGRESSIONS (${issueReport.newRegressionsCount})",
                isSelected = selectedCategoryFilter == IssueCategory.NEW_REGRESSION,
                color = HexnilError,
                onClick = { selectedCategoryFilter = IssueCategory.NEW_REGRESSION }
            )
            CategoryFilterPill(
                label = "PRE-EXISTING (${issueReport.persistedCount})",
                isSelected = selectedCategoryFilter == IssueCategory.PERSISTED,
                color = HexnilPreExisting,
                onClick = { selectedCategoryFilter = IssueCategory.PERSISTED }
            )
            CategoryFilterPill(
                label = "STABLE (${issueReport.unchangedCount})",
                isSelected = selectedCategoryFilter == IssueCategory.UNCHANGED,
                color = HexnilPrimaryText,
                onClick = { selectedCategoryFilter = IssueCategory.UNCHANGED }
            )
            CategoryFilterPill(
                label = "INSUFFICIENT (${issueReport.inconclusiveCount})",
                isSelected = selectedCategoryFilter == IssueCategory.INSUFFICIENT_EVIDENCE,
                color = HexnilSecondaryText,
                onClick = { selectedCategoryFilter = IssueCategory.INSUFFICIENT_EVIDENCE }
            )
        }

        // 3. Classified Issues List
        SectionHeader(
            title = "CLASSIFIED UPDATE ISSUES",
            actionLabel = "${filteredIssues.size} Showing",
            onActionClick = {}
        )

        filteredIssues.forEach { issue ->
            IssueClassificationCard(
                issue = issue,
                onClick = { onNavigateToMetricDetail("${issue.workloadId}_${issue.metricName}") }
            )
        }

        // 4. Prediction Accuracy Evaluation
        SectionHeader(
            title = "PREDICTION VS ACTUAL OUTCOME",
            actionLabel = "Accuracy: ${predictionSummary.accuracyPercent.toInt()}%",
            onActionClick = {}
        )

        // Contingency Stats Box
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(HexnilRadius.card))
                .border(BorderStroke(1.dp, HexnilBorder), RoundedCornerShape(HexnilRadius.card)),
            color = HexnilCard
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(12.dp),
                horizontalArrangement = Arrangement.SpaceAround
            ) {
                ContingencyPill("True Pos", "${predictionSummary.truePositives}", HexnilFixed)
                ContingencyPill("True Neg", "${predictionSummary.trueNegatives}", HexnilFixed)
                ContingencyPill("False Pos", "${predictionSummary.falsePositives}", HexnilPreExisting)
                ContingencyPill("False Neg", "${predictionSummary.falseNegatives}", HexnilError)
            }
        }

        predictionSummary.outcomes.forEach { outcome ->
            PredictionOutcomeCard(outcome = outcome)
        }

        // 5. Statistical Evidence by Metric
        SectionHeader(
            title = "MEASURED STATISTICAL METRICS",
            actionLabel = "${analysis.metricResults.size} Metrics",
            onActionClick = {}
        )

        analysis.metricResults.forEach { metric ->
            MetricCard(
                metric = metric,
                onClick = { onNavigateToMetricDetail(metric.key) }
            )
        }
    }
}

@Composable
private fun CategoryFilterPill(
    label: String,
    isSelected: Boolean,
    color: Color = HexnilMainAccent,
    onClick: () -> Unit
) {
    Surface(
        shape = RoundedCornerShape(HexnilRadius.badge),
        color = if (isSelected) color.copy(alpha = 0.2f) else HexnilSecondaryCard,
        border = BorderStroke(1.dp, if (isSelected) color else HexnilBorderSubtle),
        modifier = Modifier.clickable { onClick() }
    ) {
        Text(
            text = label,
            color = if (isSelected) color else HexnilSecondaryText,
            fontSize = 10.sp,
            fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Medium,
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
        )
    }
}

@Composable
private fun ContingencyPill(label: String, count: String, color: Color) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(text = count, color = color, fontSize = 16.sp, fontWeight = FontWeight.Bold, fontFamily = FontFamily.Monospace)
        Text(text = label, color = HexnilSecondaryText, fontSize = 10.sp)
    }
}
