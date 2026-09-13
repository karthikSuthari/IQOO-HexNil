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
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
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
import com.example.iqoo_hexnil.data.WorkloadDefinition
import com.example.iqoo_hexnil.data.WorkloadPriority
import com.example.iqoo_hexnil.ui.theme.HexnilAccentGlow
import com.example.iqoo_hexnil.ui.theme.HexnilAccentSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilBackground
import com.example.iqoo_hexnil.ui.theme.HexnilBorder
import com.example.iqoo_hexnil.ui.theme.HexnilBorderSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilCard
import com.example.iqoo_hexnil.ui.theme.HexnilMainAccent
import com.example.iqoo_hexnil.ui.theme.HexnilPrimaryText
import com.example.iqoo_hexnil.ui.theme.HexnilRadius
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryCard
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSpacing
import com.example.iqoo_hexnil.ui.theme.HexnilSuccess

@Composable
fun WorkloadCard(
    workload: WorkloadDefinition,
    isRunning: Boolean,
    onRunClick: () -> Unit,
    onCardClick: (() -> Unit)? = null,
    modifier: Modifier = Modifier
) {
    val isHighPriority = workload.priority == WorkloadPriority.HIGH
    val cardBorder = if (isHighPriority) {
        BorderStroke(1.dp, HexnilMainAccent.copy(alpha = 0.4f))
    } else {
        BorderStroke(1.dp, HexnilBorder)
    }

    val targetTelemetry = when (workload.id) {
        "startup_01" -> "Startup Latency & TTID"
        "cpu_01" -> "Computation Duration & Integer Throughput"
        "memory_01" -> "Heap Allocation & Memory Churn"
        "scroll_01" -> "Choreographer Frame Render Time"
        "video_power_01" -> "Workload Duration & Battery Current"
        else -> "System Telemetry"
    }

    Surface(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(HexnilRadius.card))
            .border(cardBorder.width, cardBorder.brush, RoundedCornerShape(HexnilRadius.card))
            .then(if (onCardClick != null) Modifier.clickable { onCardClick() } else Modifier),
        color = HexnilCard
    ) {
        Column(modifier = Modifier.padding(HexnilSpacing.cardPadding)) {
            // Top row: ID, Selection badge on left; Priority & Execution Status on right
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(HexnilSpacing.xs)
                ) {
                    Text(
                        text = workload.id,
                        color = if (isHighPriority) HexnilMainAccent else HexnilPrimaryText,
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                    if (workload.isSelected) {
                        Surface(
                            shape = RoundedCornerShape(HexnilRadius.metadata),
                            color = HexnilAccentSubtle,
                            border = BorderStroke(1.dp, HexnilMainAccent.copy(alpha = 0.5f))
                        ) {
                            Text(
                                text = "SELECTED",
                                color = HexnilMainAccent,
                                fontSize = 11.sp,
                                fontWeight = FontWeight.Bold,
                                modifier = Modifier.padding(horizontal = 7.dp, vertical = 3.dp)
                            )
                        }
                    }
                }

                Row(
                    horizontalArrangement = Arrangement.spacedBy(HexnilSpacing.xs),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    PriorityChip(priority = workload.priority)
                    WorkloadStatusChip(status = workload.status)
                }
            }

            Spacer(modifier = Modifier.height(10.dp))

            // Workload Name
            Text(
                text = workload.name,
                color = HexnilPrimaryText,
                fontSize = 17.sp,
                fontWeight = FontWeight.Bold
            )

            Spacer(modifier = Modifier.height(4.dp))

            // Workload Purpose & Telemetry Scope
            Text(
                text = workload.purpose,
                color = HexnilSecondaryText,
                fontSize = 13.sp,
                lineHeight = 19.sp
            )

            Spacer(modifier = Modifier.height(14.dp))

            // Engineering Details (Structured, zero text collisions)
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
                    EvidenceAvailabilityChip(availability = workload.evidenceAvailability)
                    Text(
                        text = "#${workload.configHash}",
                        color = HexnilSecondaryText,
                        fontSize = 11.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }
                Text(
                    text = targetTelemetry,
                    color = HexnilAccentGlow,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Medium
                )
            }

            Spacer(modifier = Modifier.height(14.dp))

            // Footer: Last measured duration + Execute Button
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(
                        text = "LAST MEASUREMENT",
                        color = HexnilSecondaryText,
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 0.5.sp
                    )
                    Spacer(modifier = Modifier.height(2.dp))
                    Text(
                        text = if (workload.lastDurationMs != null) "${"%.1f".format(workload.lastDurationMs)} ms" else "NOT RUN",
                        color = if (workload.lastDurationMs != null) HexnilSuccess else HexnilSecondaryText,
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Bold,
                        fontFamily = FontFamily.Monospace
                    )
                }

                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    if (onCardClick != null) {
                        Surface(
                            modifier = Modifier.clickable { onCardClick() },
                            shape = RoundedCornerShape(HexnilRadius.button),
                            color = HexnilSecondaryCard,
                            border = BorderStroke(1.dp, HexnilBorderSubtle)
                        ) {
                            Text(
                                text = "Inspect ➔",
                                color = HexnilSecondaryText,
                                fontSize = 13.sp,
                                fontWeight = FontWeight.Bold,
                                modifier = Modifier.padding(horizontal = 12.dp, vertical = 9.dp)
                            )
                        }
                    }

                    Button(
                        onClick = onRunClick,
                        enabled = !isRunning,
                        colors = ButtonDefaults.buttonColors(
                            containerColor = HexnilSecondaryCard,
                            contentColor = HexnilMainAccent
                        ),
                        border = BorderStroke(1.dp, HexnilMainAccent),
                        shape = RoundedCornerShape(HexnilRadius.button)
                    ) {
                        Text(
                            text = if (isRunning) "Running..." else "Execute ➔",
                            fontSize = 13.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
            }
        }
    }
}
