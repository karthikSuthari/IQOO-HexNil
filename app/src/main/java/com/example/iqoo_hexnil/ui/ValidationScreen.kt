package com.example.iqoo_hexnil.ui

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
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
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
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
import com.example.iqoo_hexnil.data.WorkloadDefinition
import com.example.iqoo_hexnil.data.WorkloadPriority
import com.example.iqoo_hexnil.ui.components.EmptyState
import com.example.iqoo_hexnil.ui.components.EvidenceAvailabilityChip
import com.example.iqoo_hexnil.ui.components.PriorityChip
import com.example.iqoo_hexnil.ui.components.WorkloadCard
import com.example.iqoo_hexnil.ui.components.WorkloadStatusChip
import com.example.iqoo_hexnil.ui.theme.HexnilAccentGlow
import com.example.iqoo_hexnil.ui.theme.HexnilAccentSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilBackground
import com.example.iqoo_hexnil.ui.theme.HexnilBorder
import com.example.iqoo_hexnil.ui.theme.HexnilBorderSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilCard
import com.example.iqoo_hexnil.ui.theme.HexnilInfo
import com.example.iqoo_hexnil.ui.theme.HexnilMainAccent
import com.example.iqoo_hexnil.ui.theme.HexnilPrimaryText
import com.example.iqoo_hexnil.ui.theme.HexnilRadius
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryCard
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSpacing
import com.example.iqoo_hexnil.ui.theme.HexnilSuccess
import com.example.iqoo_hexnil.ui.theme.HexnilWarning

@Composable
fun ValidationScreen(
    workloads: List<WorkloadDefinition>,
    onRunWorkloadAction: (String, String) -> Unit,
    modifier: Modifier = Modifier
) {
    val scrollState = rememberScrollState()
    var runningWorkloadId by remember { mutableStateOf<String?>(null) }
    var inspectingWorkload by remember { mutableStateOf<WorkloadDefinition?>(null) }
    var selectedPriorityFilter by remember { mutableStateOf<WorkloadPriority?>(null) }
    var workloadDurations by remember {
        mutableStateOf(workloads.associate { it.id to (it.lastDurationMs ?: 5000.0) })
    }

    val filteredWorkloads = if (selectedPriorityFilter != null) {
        workloads.filter { it.priority == selectedPriorityFilter }
    } else {
        workloads
    }

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(HexnilBackground)
            .padding(horizontal = HexnilSpacing.screenHorizontal, vertical = HexnilSpacing.screenVertical)
            .verticalScroll(scrollState),
        verticalArrangement = Arrangement.spacedBy(HexnilSpacing.sectionSpacing)
    ) {
        // Validation Engine Header Card
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(HexnilRadius.card))
                .border(1.dp, HexnilBorderSubtle, RoundedCornerShape(HexnilRadius.card)),
            color = HexnilCard
        ) {
            Column(modifier = Modifier.padding(HexnilSpacing.cardPadding)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "DECLARATIVE WORKLOAD ENGINE",
                        color = HexnilMainAccent,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 1.sp
                    )
                    Surface(
                        shape = RoundedCornerShape(HexnilRadius.metadata),
                        color = HexnilSecondaryCard,
                        border = BorderStroke(1.dp, HexnilBorderSubtle)
                    ) {
                        Text(
                            text = "${workloads.size} WORKLOADS LOCKED",
                            color = HexnilAccentGlow,
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            fontFamily = FontFamily.Monospace,
                            modifier = Modifier.padding(horizontal = 8.dp, vertical = 3.dp)
                        )
                    }
                }

                Spacer(modifier = Modifier.height(10.dp))
                Text(
                    text = "5 Locked Declarative Benchmarks",
                    color = HexnilPrimaryText,
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(6.dp))
                Text(
                    text = "Enforces reproducible execution on physical Android hardware with pre-run thermal stabilization, battery gatekeeping, and immutable random seed (42). Tap any workload to inspect its execution contract.",
                    color = HexnilSecondaryText,
                    fontSize = 13.sp,
                    lineHeight = 19.sp
                )
            }
        }

        // Priority Filter Chips Row
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            WorkloadFilterChip(
                label = "ALL (${workloads.size})",
                isSelected = selectedPriorityFilter == null,
                color = HexnilMainAccent,
                onClick = { selectedPriorityFilter = null },
                modifier = Modifier.weight(1f)
            )
            WorkloadFilterChip(
                label = "HIGH (${workloads.count { it.priority == WorkloadPriority.HIGH }})",
                isSelected = selectedPriorityFilter == WorkloadPriority.HIGH,
                color = HexnilWarning,
                onClick = { selectedPriorityFilter = WorkloadPriority.HIGH },
                modifier = Modifier.weight(1f)
            )
            WorkloadFilterChip(
                label = "MEDIUM (${workloads.count { it.priority == WorkloadPriority.MEDIUM }})",
                isSelected = selectedPriorityFilter == WorkloadPriority.MEDIUM,
                color = HexnilInfo,
                onClick = { selectedPriorityFilter = WorkloadPriority.MEDIUM },
                modifier = Modifier.weight(1f)
            )
        }

        if (filteredWorkloads.isEmpty()) {
            EmptyState(
                title = "No Workloads In Category",
                message = "Select 'ALL' to view all declarative workloads."
            )
        } else {
            // Workload Cards
            filteredWorkloads.forEach { workload ->
                val isRunning = runningWorkloadId == workload.id
                val currentDuration = workloadDurations[workload.id] ?: workload.lastDurationMs

                WorkloadCard(
                    workload = workload.copy(lastDurationMs = currentDuration),
                    isRunning = isRunning,
                    onCardClick = { inspectingWorkload = workload },
                    onRunClick = {
                        runningWorkloadId = workload.id
                        onRunWorkloadAction(workload.id, workload.action)
                        workloadDurations = workloadDurations + (workload.id to (currentDuration ?: 5000.0))
                        runningWorkloadId = null
                    }
                )
            }
        }

        Spacer(modifier = Modifier.height(16.dp))
    }

    // Workload Inspection Panel Dialog
    inspectingWorkload?.let { wl ->
        val targetMeasurements = when (wl.id) {
            "startup_01" -> "Startup Latency (TTID), Application Process Fork, Cold Start Overhead"
            "cpu_01" -> "Computation Duration, Integer Math Throughput, Thread Execution State"
            "memory_01" -> "JVM Heap Allocation, Retained Memory, Garbage Collection Churn"
            "scroll_01" -> "Choreographer Frame Render Time, 95th Percentile Janks, VSync Deadlines"
            "video_power_01" -> "Workload Duration, Battery Drain Current, Thermal Dissipation"
            else -> "System Telemetry and Execution Latency"
        }

        AlertDialog(
            onDismissRequest = { inspectingWorkload = null },
            containerColor = HexnilCard,
            titleContentColor = HexnilPrimaryText,
            textContentColor = HexnilSecondaryText,
            shape = RoundedCornerShape(HexnilRadius.hero),
            title = {
                Column(modifier = Modifier.fillMaxWidth()) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "INSPECTION PANEL",
                            color = HexnilMainAccent,
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            letterSpacing = 1.sp
                        )
                        PriorityChip(priority = wl.priority)
                    }
                    Spacer(modifier = Modifier.height(6.dp))
                    Text(
                        text = "${wl.id.uppercase()} — ${wl.name}",
                        color = HexnilPrimaryText,
                        fontSize = 16.sp,
                        fontWeight = FontWeight.Bold
                    )
                }
            },
            text = {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .verticalScroll(rememberScrollState()),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    // SECTION 1: PURPOSE
                    InspectionSectionBlock(
                        title = "1. PURPOSE",
                        content = wl.purpose
                    )

                    Box(modifier = Modifier.fillMaxWidth().height(1.dp).background(HexnilBorder.copy(alpha = 0.5f)))

                    // SECTION 2: WHY SELECTED
                    InspectionSectionBlock(
                        title = "2. WHY SELECTED",
                        content = "Mandatory declarative benchmark locked under Phase 3. Configured to detect regressions in ${wl.name.lowercase()} with deterministic execution reproducibility across V0 and V1 builds."
                    )

                    Box(modifier = Modifier.fillMaxWidth().height(1.dp).background(HexnilBorder.copy(alpha = 0.5f)))

                    // SECTION 3: MEASUREMENTS
                    InspectionSectionBlock(
                        title = "3. MEASUREMENTS",
                        content = targetMeasurements
                    )

                    Box(modifier = Modifier.fillMaxWidth().height(1.dp).background(HexnilBorder.copy(alpha = 0.5f)))

                    // SECTION 4: PRECONDITIONS
                    InspectionSectionBlock(
                        title = "4. PRECONDITIONS",
                        content = "Battery Level ≥ 20% · Thermal State ≤ NORMAL (0-1) · Device Screen ON · Background Benchmarks Suspended"
                    )

                    Box(modifier = Modifier.fillMaxWidth().height(1.dp).background(HexnilBorder.copy(alpha = 0.5f)))

                    // SECTION 5: EXECUTION PARAMETERS (Clean typographic list, no nested card)
                    Column(
                        modifier = Modifier.fillMaxWidth(),
                        verticalArrangement = Arrangement.spacedBy(3.dp)
                    ) {
                        Text(
                            text = "5. EXECUTION PARAMETERS",
                            color = HexnilAccentGlow,
                            fontSize = 10.sp,
                            fontWeight = FontWeight.Bold,
                            letterSpacing = 0.5.sp
                        )
                        InspectionPropertyRow("Action Intent", wl.action, isMonospace = true)
                        InspectionPropertyRow("Config Hash", "#${wl.configHash}", isMonospace = true)
                        InspectionPropertyRow("Deterministic Seed", "42 (Locked)", isMonospace = true)
                        InspectionPropertyRow("Matched Runs", "${wl.matchedRunsCount} iterations", isMonospace = true)
                    }

                    Box(modifier = Modifier.fillMaxWidth().height(1.dp).background(HexnilBorder.copy(alpha = 0.5f)))

                    // SECTION 6: EVIDENCE STATUS (Clean typographic list, no nested card)
                    Column(
                        modifier = Modifier.fillMaxWidth(),
                        verticalArrangement = Arrangement.spacedBy(3.dp)
                    ) {
                        Text(
                            text = "6. EVIDENCE STATUS",
                            color = HexnilAccentGlow,
                            fontSize = 10.sp,
                            fontWeight = FontWeight.Bold,
                            letterSpacing = 0.5.sp
                        )
                        InspectionPropertyRow("Availability", wl.evidenceAvailability)
                        InspectionPropertyRow("Selection State", if (wl.isSelected) "LOCKED & SELECTED" else "OPTIONAL")
                        InspectionPropertyRow("Last Baseline Duration", "${String.format("%.1f", wl.lastDurationMs ?: 5000.0)} ms", isMonospace = true)
                        InspectionPropertyRow("Threshold Target", "5.0% Engineering Margin")
                    }
                }
            },
            confirmButton = {
                Button(
                    onClick = {
                        val currentWl = inspectingWorkload
                        inspectingWorkload = null
                        if (currentWl != null) {
                            runningWorkloadId = currentWl.id
                            onRunWorkloadAction(currentWl.id, currentWl.action)
                            runningWorkloadId = null
                        }
                    },
                    colors = ButtonDefaults.buttonColors(
                        containerColor = HexnilMainAccent,
                        contentColor = Color.White
                    ),
                    shape = RoundedCornerShape(HexnilRadius.button)
                ) {
                    Text(
                        text = "Use Workload ➔",
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold
                    )
                }
            },
            dismissButton = {
                Button(
                    onClick = { inspectingWorkload = null },
                    colors = ButtonDefaults.buttonColors(
                        containerColor = HexnilSecondaryCard,
                        contentColor = HexnilSecondaryText
                    ),
                    border = BorderStroke(1.dp, HexnilBorder),
                    shape = RoundedCornerShape(HexnilRadius.button)
                ) {
                    Text(
                        text = "Close",
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Medium
                    )
                }
            }
        )
    }
}

@Composable
private fun WorkloadFilterChip(
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
            fontSize = 12.sp,
            fontWeight = if (isSelected) FontWeight.Bold else FontWeight.SemiBold,
            modifier = Modifier.padding(vertical = 10.dp, horizontal = 6.dp),
            maxLines = 1
        )
    }
}

@Composable
private fun InspectionPropertyRow(
    label: String,
    value: String,
    isMonospace: Boolean = false
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(text = label, color = HexnilSecondaryText, fontSize = 13.sp)
        Text(
            text = value,
            color = if (isMonospace) HexnilAccentGlow else HexnilPrimaryText,
            fontSize = 13.sp,
            fontWeight = if (isMonospace) FontWeight.Bold else FontWeight.Medium,
            fontFamily = if (isMonospace) FontFamily.Monospace else FontFamily.Default
        )
    }
}

@Composable
private fun InspectionSectionBlock(
    title: String,
    content: String
) {
    Column(
        modifier = Modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(4.dp)
    ) {
        Text(
            text = title,
            color = HexnilAccentGlow,
            fontSize = 12.sp,
            fontWeight = FontWeight.Bold,
            letterSpacing = 0.5.sp
        )
        Text(
            text = content,
            color = HexnilPrimaryText,
            fontSize = 14.sp,
            lineHeight = 20.sp
        )
    }
}
