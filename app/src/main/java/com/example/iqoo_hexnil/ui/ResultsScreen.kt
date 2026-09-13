package com.example.iqoo_hexnil.ui

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
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
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.iqoo_hexnil.data.ComparisonAnalysis
import com.example.iqoo_hexnil.data.VerdictType
import com.example.iqoo_hexnil.ui.components.EvidenceCoverageCard
import com.example.iqoo_hexnil.ui.components.MetricCard
import com.example.iqoo_hexnil.ui.components.SectionHeader
import com.example.iqoo_hexnil.ui.theme.HexnilAccentSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilBackground
import com.example.iqoo_hexnil.ui.theme.HexnilBorder
import com.example.iqoo_hexnil.ui.theme.HexnilCard
import com.example.iqoo_hexnil.ui.theme.HexnilMainAccent
import com.example.iqoo_hexnil.ui.theme.HexnilPrimaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryCard
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSuccess
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
        // Evidence Coverage Summary Card
        EvidenceCoverageCard(analysis = analysis)

        // Filter Chips Row
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(6.dp)
        ) {
            FilterVerdictChip(
                label = "ALL (13)",
                isSelected = selectedFilter == null,
                color = HexnilMainAccent,
                onClick = { selectedFilter = null },
                modifier = Modifier.weight(1f)
            )
            FilterVerdictChip(
                label = "UNCHANGED (8)",
                isSelected = selectedFilter == VerdictType.UNCHANGED,
                color = HexnilSuccess,
                onClick = { selectedFilter = VerdictType.UNCHANGED },
                modifier = Modifier.weight(1f)
            )
            FilterVerdictChip(
                label = "INCONCL. (5)",
                isSelected = selectedFilter == VerdictType.INCONCLUSIVE,
                color = HexnilWarning,
                onClick = { selectedFilter = VerdictType.INCONCLUSIVE },
                modifier = Modifier.weight(1f)
            )
        }

        // Section Title
        SectionHeader(
            category = "STATISTICAL EVALUATION TABLE",
            subtitle = "Tap any metric card to inspect raw run observations, 95% CI, p-value, and threshold reasoning."
        )

        // List of Metric Cards
        filteredMetrics.forEach { metric ->
            MetricCard(
                metric = metric,
                onClick = { onNavigateToMetricDetail(metric.key) }
            )
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
        modifier = modifier
            .clickable { onClick() },
        shape = RoundedCornerShape(6.dp),
        color = bgColor,
        border = BorderStroke(1.dp, borderColor)
    ) {
        Text(
            text = label,
            color = if (isSelected) color else HexnilSecondaryText,
            fontSize = 10.sp,
            fontWeight = if (isSelected) FontWeight.Bold else FontWeight.SemiBold,
            modifier = Modifier.padding(vertical = 8.dp, horizontal = 4.dp),
            maxLines = 1
        )
    }
}
