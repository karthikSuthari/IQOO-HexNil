package com.example.iqoo_hexnil.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
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
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.iqoo_hexnil.data.WorkloadDefinition
import com.example.iqoo_hexnil.ui.components.WorkloadCard
import com.example.iqoo_hexnil.ui.theme.HexnilBackground
import com.example.iqoo_hexnil.ui.theme.HexnilBorder
import com.example.iqoo_hexnil.ui.theme.HexnilCard
import com.example.iqoo_hexnil.ui.theme.HexnilMainAccent
import com.example.iqoo_hexnil.ui.theme.HexnilPrimaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryText

@Composable
fun ValidationScreen(
    workloads: List<WorkloadDefinition>,
    onRunWorkloadAction: (String, String) -> Unit,
    modifier: Modifier = Modifier
) {
    val scrollState = rememberScrollState()
    var runningWorkloadId by remember { mutableStateOf<String?>(null) }
    var workloadDurations by remember {
        mutableStateOf(workloads.associate { it.id to (it.lastDurationMs ?: 5000.0) })
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
                Text(
                    text = "DETERMINISTIC VALIDATION SUITE (PHASE 3)",
                    color = HexnilMainAccent,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp
                )
                Spacer(modifier = Modifier.height(6.dp))
                Text(
                    text = "5 Locked Declarative Workloads",
                    color = HexnilPrimaryText,
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = "Workloads enforce reproducible execution on physical Android hardware with capability-aware telemetry capture.",
                    color = HexnilSecondaryText,
                    fontSize = 12.sp,
                    lineHeight = 16.sp
                )
            }
        }

        // Workload Cards
        workloads.forEach { workload ->
            val isRunning = runningWorkloadId == workload.id
            val currentDuration = workloadDurations[workload.id] ?: workload.lastDurationMs

            WorkloadCard(
                workload = workload.copy(lastDurationMs = currentDuration),
                isRunning = isRunning,
                onRunClick = {
                    runningWorkloadId = workload.id
                    onRunWorkloadAction(workload.id, workload.action)
                    // Keep duration updated
                    workloadDurations = workloadDurations + (workload.id to (currentDuration ?: 5000.0))
                    runningWorkloadId = null
                }
            )
        }

        Spacer(modifier = Modifier.height(16.dp))
    }
}
