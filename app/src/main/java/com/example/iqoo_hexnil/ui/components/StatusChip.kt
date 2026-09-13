package com.example.iqoo_hexnil.ui.components

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
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
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.iqoo_hexnil.data.ClaimRiskLevel
import com.example.iqoo_hexnil.data.WorkloadPriority
import com.example.iqoo_hexnil.data.WorkloadStatus
import com.example.iqoo_hexnil.ui.theme.HexnilBorder
import com.example.iqoo_hexnil.ui.theme.HexnilError
import com.example.iqoo_hexnil.ui.theme.HexnilErrorSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilInfo
import com.example.iqoo_hexnil.ui.theme.HexnilInfoSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryCard
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSuccess
import com.example.iqoo_hexnil.ui.theme.HexnilSuccessSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilWarning
import com.example.iqoo_hexnil.ui.theme.HexnilWarningSubtle

@Composable
fun WorkloadStatusChip(
    status: WorkloadStatus,
    modifier: Modifier = Modifier
) {
    val (bgColor, fgColor) = when (status) {
        WorkloadStatus.COMPLETED -> Pair(HexnilSuccessSubtle, HexnilSuccess)
        WorkloadStatus.RUNNING -> Pair(HexnilInfoSubtle, HexnilInfo)
        WorkloadStatus.QUEUED -> Pair(HexnilSecondaryCard, HexnilSecondaryText)
        WorkloadStatus.SKIPPED -> Pair(HexnilSecondaryCard, HexnilSecondaryText)
        WorkloadStatus.INCONCLUSIVE -> Pair(HexnilWarningSubtle, HexnilWarning)
        WorkloadStatus.FAILED -> Pair(HexnilErrorSubtle, HexnilError)
    }

    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(4.dp),
        color = bgColor,
        border = BorderStroke(1.dp, fgColor.copy(alpha = 0.5f))
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(5.dp)
                    .background(fgColor, CircleShape)
            )
            Spacer(modifier = Modifier.width(4.dp))
            Text(
                text = status.label.uppercase(),
                color = fgColor,
                fontSize = 9.sp,
                fontWeight = FontWeight.Bold,
                letterSpacing = 0.5.sp,
                maxLines = 1
            )
        }
    }
}

@Composable
fun PriorityChip(
    priority: WorkloadPriority,
    modifier: Modifier = Modifier
) {
    val fgColor = when (priority) {
        WorkloadPriority.HIGH -> HexnilWarning
        WorkloadPriority.MEDIUM -> HexnilInfo
        WorkloadPriority.LOW -> HexnilSecondaryText
    }

    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(4.dp),
        color = HexnilSecondaryCard,
        border = BorderStroke(1.dp, HexnilBorder)
    ) {
        Text(
            text = "${priority.label} PRIORITY",
            color = fgColor,
            fontSize = 9.sp,
            fontWeight = FontWeight.Bold,
            modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp),
            maxLines = 1
        )
    }
}

@Composable
fun RiskChip(
    riskLevel: ClaimRiskLevel,
    modifier: Modifier = Modifier
) {
    val (bgColor, fgColor) = when (riskLevel) {
        ClaimRiskLevel.HIGH -> Pair(HexnilErrorSubtle, HexnilError)
        ClaimRiskLevel.MODERATE -> Pair(HexnilWarningSubtle, HexnilWarning)
        ClaimRiskLevel.LOW -> Pair(HexnilSuccessSubtle, HexnilSuccess)
    }

    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(4.dp),
        color = bgColor,
        border = BorderStroke(1.dp, fgColor.copy(alpha = 0.5f))
    ) {
        Text(
            text = riskLevel.label.uppercase(),
            color = fgColor,
            fontSize = 9.sp,
            fontWeight = FontWeight.Bold,
            modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp),
            maxLines = 1
        )
    }
}

@Composable
fun ValidationStatusChip(
    status: String,
    modifier: Modifier = Modifier
) {
    val (bgColor, fgColor) = when (status.uppercase()) {
        "SUPPORTED" -> Pair(HexnilSuccessSubtle, HexnilSuccess)
        "PARTIAL" -> Pair(HexnilWarningSubtle, HexnilWarning)
        "UNCHANGED" -> Pair(HexnilSecondaryCard, HexnilSuccess)
        "INCONCLUSIVE" -> Pair(HexnilWarningSubtle, HexnilWarning)
        "UNSUPPORTED" -> Pair(HexnilSecondaryCard, HexnilSecondaryText)
        else -> Pair(HexnilSecondaryCard, HexnilSecondaryText)
    }

    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(4.dp),
        color = bgColor,
        border = BorderStroke(1.dp, fgColor.copy(alpha = 0.5f))
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(5.dp)
                    .background(fgColor, CircleShape)
            )
            Spacer(modifier = Modifier.width(4.dp))
            Text(
                text = status.uppercase(),
                color = fgColor,
                fontSize = 9.sp,
                fontWeight = FontWeight.Bold,
                letterSpacing = 0.5.sp,
                maxLines = 1
            )
        }
    }
}

@Composable
fun EvidenceAvailabilityChip(
    availability: String,
    modifier: Modifier = Modifier
) {
    val (bgColor, fgColor) = when (availability.uppercase()) {
        "AVAILABLE" -> Pair(HexnilSuccessSubtle, HexnilSuccess)
        "NOT_RUN", "NOT RUN" -> Pair(HexnilSecondaryCard, HexnilSecondaryText)
        "UNSUPPORTED" -> Pair(HexnilSecondaryCard, HexnilSecondaryText)
        "INCONCLUSIVE" -> Pair(HexnilWarningSubtle, HexnilWarning)
        else -> Pair(HexnilSecondaryCard, HexnilSecondaryText)
    }

    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(4.dp),
        color = bgColor,
        border = BorderStroke(1.dp, fgColor.copy(alpha = 0.4f))
    ) {
        Text(
            text = availability.replace("_", " ").uppercase(),
            color = fgColor,
            fontSize = 9.sp,
            fontWeight = FontWeight.Bold,
            modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp),
            maxLines = 1
        )
    }
}

