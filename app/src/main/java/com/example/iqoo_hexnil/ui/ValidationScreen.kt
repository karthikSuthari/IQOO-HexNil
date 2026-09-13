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
import com.example.iqoo_hexnil.ui.theme.HexnilCard
import com.example.iqoo_hexnil.ui.theme.HexnilInfo
import com.example.iqoo_hexnil.ui.theme.HexnilMainAccent
import com.example.iqoo_hexnil.ui.theme.HexnilPrimaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryCard
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryText
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
            .padding(horizontal = 16.dp, vertical = 12.dp)
            .verticalScroll(scrollState),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        // Validation Engine Header Card
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
                        text = "DETERMINISTIC WORKLOAD ENGINE (PHASE 3)",
                        color = HexnilMainAccent,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 1.sp
                    )
                    Surface(
                        shape = RoundedCornerShape(4.dp),
                        color = HexnilSecondaryCard,
                        border = BorderStroke(1.dp, HexnilBorder)
                    ) {
                        Text(
                            text = "${workloads.size} WORKLOADS LOCKED",
                            color = HexnilAccentGlow,
                            fontSize = 9.sp,
                            fontWeight = FontWeight.Bold,
                            fontFamily = FontFamily.Monospace,
                            modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                        )
                    }
                }

                Spacer(modifier = Modifier.height(6.dp))
                Text(
                    text = "5 Locked Declarative Benchmarks",
                    color = HexnilPrimaryText,
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = "Enforces reproducible execution on physical Android hardware with pre-run thermal stabilization, battery gatekeeping, and immutable random seed (42). Tap any workload to inspect its execution contract.",
                    color = HexnilSecondaryText,
                    fontSize = 12.sp,
                    lineHeight = 16.sp
                )
            }
        }

        // Priority Filter Chips Row
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(6.dp)
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

    // Workload Inspection Modal Dialog
    inspectingWorkload?.let { wl ->
        AlertDialog(
            onDismissRequest = { inspectingWorkload = null },
            containerColor = HexnilCard,
            titleContentColor = HexnilPrimaryText,
            textContentColor = HexnilSecondaryText,
            title = {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = wl.id,
                        color = HexnilMainAccent,
                        fontSize = 15.sp,
                        fontFamily = FontFamily.Monospace,
                        fontWeight = FontWeight.Bold
                    )
                    PriorityChip(priority = wl.priority)
                }
            },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text(text = wl.name, color = HexnilPrimaryText, fontSize = 14.sp, fontWeight = FontWeight.Bold)
                    Text(text = wl.description, color = HexnilSecondaryText, fontSize = 12.sp, lineHeight = 16.sp)

                    Surface(
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(6.dp),
                        color = HexnilSecondaryCard,
                        border = BorderStroke(1.dp, HexnilBorder)
                    ) {
                        Column(modifier = Modifier.padding(10.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                            InspectionPropertyRow("Purpose", wl.purpose)
                            InspectionPropertyRow("Action", wl.action, isMonospace = true)
                            InspectionPropertyRow("Config Hash", "#${wl.configHash}", isMonospace = true)
                            InspectionPropertyRow("Matched Runs", "${wl.matchedRunsCount} iterations")
                            InspectionPropertyRow("Selection State", if (wl.isSelected) "SELECTED" else "NOT SELECTED")
                            InspectionPropertyRow("Evidence State", wl.evidenceAvailability)
                            InspectionPropertyRow("Preconditions", "Battery >= 20%, Thermal <= 1")
                            InspectionPropertyRow("Random Seed", "42 (Locked)")
                        }
                    }
                }
            },
            confirmButton = {
                Button(
                    onClick = { inspectingWorkload = null },
                    colors = ButtonDefaults.buttonColors(
                        containerColor = HexnilSecondaryCard,
                        contentColor = HexnilMainAccent
                    ),
                    border = BorderStroke(1.dp, HexnilMainAccent),
                    shape = RoundedCornerShape(6.dp)
                ) {
                    Text(text = "Close Inspection", fontSize = 12.sp, fontWeight = FontWeight.Bold)
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
            fontSize = 10.sp,
            fontWeight = if (isSelected) FontWeight.Bold else FontWeight.SemiBold,
            modifier = Modifier.padding(vertical = 8.dp, horizontal = 4.dp),
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
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.Top
    ) {
        Text(text = label, color = HexnilSecondaryText, fontSize = 10.sp, modifier = Modifier.weight(0.4f))
        Text(
            text = value,
            color = if (isMonospace) HexnilAccentGlow else HexnilPrimaryText,
            fontSize = 10.sp,
            fontWeight = FontWeight.Medium,
            fontFamily = if (isMonospace) FontFamily.Monospace else FontFamily.Default,
            modifier = Modifier.weight(0.6f)
        )
    }
}
