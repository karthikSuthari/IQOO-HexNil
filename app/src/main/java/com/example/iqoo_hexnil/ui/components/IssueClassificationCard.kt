package com.example.iqoo_hexnil.ui.components

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
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
import com.example.iqoo_hexnil.data.IssueCategory
import com.example.iqoo_hexnil.data.IssueClassification
import com.example.iqoo_hexnil.ui.theme.HexnilBorder
import com.example.iqoo_hexnil.ui.theme.HexnilBorderSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilCard
import com.example.iqoo_hexnil.ui.theme.HexnilError
import com.example.iqoo_hexnil.ui.theme.HexnilErrorSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilFixed
import com.example.iqoo_hexnil.ui.theme.HexnilFixedSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilPreExisting
import com.example.iqoo_hexnil.ui.theme.HexnilPreExistingSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilPrimaryText
import com.example.iqoo_hexnil.ui.theme.HexnilRadius
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryCard
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryText

@Composable
fun IssueClassificationCard(
    issue: IssueClassification,
    onClick: (() -> Unit)? = null,
    modifier: Modifier = Modifier
) {
    val categoryColor = when (issue.category) {
        IssueCategory.NEW_REGRESSION -> HexnilError
        IssueCategory.PERSISTED_WORSENED -> HexnilError
        IssueCategory.PERSISTED -> HexnilPreExisting
        IssueCategory.FIXED -> HexnilFixed
        IssueCategory.NEW_IMPROVEMENT -> HexnilFixed
        IssueCategory.UNCHANGED -> HexnilSecondaryText
        IssueCategory.INSUFFICIENT_EVIDENCE -> HexnilSecondaryText
    }

    val categorySubtleBg = when (issue.category) {
        IssueCategory.NEW_REGRESSION -> HexnilErrorSubtle
        IssueCategory.PERSISTED_WORSENED -> HexnilErrorSubtle
        IssueCategory.PERSISTED -> HexnilPreExistingSubtle
        IssueCategory.FIXED -> HexnilFixedSubtle
        IssueCategory.NEW_IMPROVEMENT -> HexnilFixedSubtle
        IssueCategory.UNCHANGED -> HexnilSecondaryCard
        IssueCategory.INSUFFICIENT_EVIDENCE -> HexnilSecondaryCard
    }

    val iconSymbol = when (issue.category) {
        IssueCategory.NEW_REGRESSION -> "🚨"
        IssueCategory.PERSISTED_WORSENED -> "⚠️"
        IssueCategory.PERSISTED -> "⏳"
        IssueCategory.FIXED -> "✅"
        IssueCategory.NEW_IMPROVEMENT -> "⚡"
        IssueCategory.UNCHANGED -> "⚖"
        IssueCategory.INSUFFICIENT_EVIDENCE -> "ℹ️"
    }

    Surface(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(HexnilRadius.card))
            .border(BorderStroke(1.dp, categoryColor.copy(alpha = 0.5f)), RoundedCornerShape(HexnilRadius.card))
            .then(if (onClick != null) Modifier.clickable { onClick() } else Modifier),
        color = HexnilCard
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            // Category Badge & Workload ID Tag
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Surface(
                    shape = RoundedCornerShape(HexnilRadius.badge),
                    color = categorySubtleBg,
                    border = BorderStroke(1.dp, categoryColor.copy(alpha = 0.6f))
                ) {
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 3.dp)
                    ) {
                        Text(text = iconSymbol, fontSize = 11.sp)
                        Spacer(modifier = Modifier.width(4.dp))
                        Text(
                            text = issue.category.label.uppercase(),
                            color = categoryColor,
                            fontSize = 10.sp,
                            fontWeight = FontWeight.Bold,
                            letterSpacing = 0.5.sp
                        )
                    }
                }

                Text(
                    text = issue.workloadId,
                    color = HexnilSecondaryText,
                    fontSize = 11.sp,
                    fontFamily = FontFamily.Monospace
                )
            }

            Spacer(modifier = Modifier.height(8.dp))

            // Metric Display Name
            Text(
                text = issue.displayName,
                color = HexnilPrimaryText,
                fontSize = 14.sp,
                fontWeight = FontWeight.Bold
            )

            Spacer(modifier = Modifier.height(4.dp))

            // Pre-existing condition callout (if applicable)
            if (issue.preUpdateAnomalyExisted && issue.preUpdateAnomalyDescription != null) {
                Surface(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(HexnilRadius.xs),
                    color = HexnilPreExistingSubtle,
                    border = BorderStroke(1.dp, HexnilPreExisting.copy(alpha = 0.4f))
                ) {
                    Row(
                        modifier = Modifier.padding(8.dp),
                        verticalAlignment = Alignment.Top
                    ) {
                        Text(text = "🔎", fontSize = 11.sp)
                        Spacer(modifier = Modifier.width(6.dp))
                        Text(
                            text = "Pre-Update V0 Context: ${issue.preUpdateAnomalyDescription}",
                            color = HexnilPreExisting,
                            fontSize = 11.sp,
                            lineHeight = 15.sp
                        )
                    }
                }
                Spacer(modifier = Modifier.height(8.dp))
            }

            // Delta & Explanation
            Text(
                text = issue.explanation,
                color = HexnilSecondaryText,
                fontSize = 12.sp,
                lineHeight = 16.sp
            )

            if (issue.percentDelta != null) {
                Spacer(modifier = Modifier.height(6.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    val sign = if (issue.percentDelta >= 0) "+" else ""
                    Text(
                        text = "Measured Delta: ${sign}${issue.percentDelta}%",
                        color = categoryColor,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )

                    if (issue.pValue != null) {
                        Text(
                            text = "p-value: ${issue.pValue}",
                            color = HexnilSecondaryText,
                            fontSize = 10.sp,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                }
            }
        }
    }
}
