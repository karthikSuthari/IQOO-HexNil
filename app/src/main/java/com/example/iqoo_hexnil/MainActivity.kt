package com.example.iqoo_hexnil

import android.content.Intent
import android.os.Bundle
import android.os.SystemClock
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Image
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
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.iqoo_hexnil.telemetry.TelemetryEngine
import com.example.iqoo_hexnil.telemetry.TelemetryRecord
import com.example.iqoo_hexnil.ui.AppScreen
import com.example.iqoo_hexnil.ui.DashboardScreen
import com.example.iqoo_hexnil.ui.StatsScreen
import com.example.iqoo_hexnil.ui.TelemetryScreen
import com.example.iqoo_hexnil.ui.WorkloadsScreen
import com.example.iqoo_hexnil.ui.theme.HexnilAccentGlow
import com.example.iqoo_hexnil.ui.theme.HexnilBackground
import com.example.iqoo_hexnil.ui.theme.HexnilBorder
import com.example.iqoo_hexnil.ui.theme.HexnilCard
import com.example.iqoo_hexnil.ui.theme.HexnilMainAccent
import com.example.iqoo_hexnil.ui.theme.HexnilPrimaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryCard
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryText
import com.example.iqoo_hexnil.ui.theme.IQOOHEXNILTheme

class MainActivity : ComponentActivity() {

    private val activityCreateTime = SystemClock.elapsedRealtime()
    private var pendingExperimentId: String? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        handleIncomingIntent(intent)

        setContent {
            IQOOHEXNILTheme {
                HexnilMainApp(
                    activityCreateTime = activityCreateTime,
                    initialExperimentId = pendingExperimentId,
                    onExecuteSession = { expId, wid, action, ops ->
                        TelemetryEngine.executeSession(
                            context = this@MainActivity,
                            experimentId = expId,
                            workloadId = wid,
                            action = action,
                            operations = ops
                        )
                    }
                )
            }
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        handleIncomingIntent(intent)
    }

    private fun handleIncomingIntent(intent: Intent?) {
        if (intent != null && intent.action == "com.example.iqoo_hexnil.ACTION_RUN_WORKLOAD") {
            pendingExperimentId = intent.getStringExtra("experiment_id")
            val workloadId = intent.getStringExtra("workload_id") ?: "startup_basic"
            val iteration = intent.getIntExtra("iteration", 1)
            val action = intent.getStringExtra("workload_action") ?: "compute_work"
            val operations = intent.getIntExtra("operations_count", 5000)
            val expId = pendingExperimentId ?: "EXP-LOCAL-001"
            TelemetryEngine.executeSession(
                context = this,
                experimentId = expId,
                workloadId = workloadId,
                iteration = iteration,
                action = action,
                operations = operations
            )
        }
    }
}

@Composable
fun HexnilMainApp(
    activityCreateTime: Long,
    initialExperimentId: String?,
    onExecuteSession: (String, String, String, Int) -> List<TelemetryRecord>
) {
    var currentScreen by remember { mutableStateOf(AppScreen.DASHBOARD) }
    var currentExperimentId by remember {
        mutableStateOf(initialExperimentId ?: "EXP-READY-001")
    }
    var telemetryRecords by remember { mutableStateOf<List<TelemetryRecord>>(emptyList()) }
    var isRunning by remember { mutableStateOf(false) }

    // Measure startup time on first launch
    LaunchedEffect(Unit) {
        val startupDuration = SystemClock.elapsedRealtime() - activityCreateTime
        TelemetryEngine.lastStartupDurationMs = startupDuration
        telemetryRecords = onExecuteSession(currentExperimentId, "startup_basic", "launch_app", 1)
    }

    Scaffold(
        modifier = Modifier.fillMaxSize(),
        containerColor = HexnilBackground,
        topBar = {
            HexnilTopAppBar(currentScreen = currentScreen)
        },
        bottomBar = {
            HexnilBottomNavBar(
                currentScreen = currentScreen,
                onScreenSelected = { currentScreen = it }
            )
        }
    ) { innerPadding ->
        Box(modifier = Modifier.padding(innerPadding)) {
            when (currentScreen) {
                AppScreen.DASHBOARD -> DashboardScreen(
                    experimentId = currentExperimentId,
                    telemetryRecords = telemetryRecords,
                    onNavigateToWorkloads = { currentScreen = AppScreen.WORKLOADS }
                )
                AppScreen.TELEMETRY -> TelemetryScreen(
                    records = telemetryRecords,
                    isRunning = isRunning,
                    onCollectSnapshot = {
                        isRunning = true
                        telemetryRecords = onExecuteSession(currentExperimentId, "snapshot", "collect_snapshot", 1)
                        isRunning = false
                    }
                )
                AppScreen.WORKLOADS -> WorkloadsScreen(
                    onRunWorkloadAction = { wid, action ->
                        isRunning = true
                        telemetryRecords = onExecuteSession(currentExperimentId, wid, action, 5000)
                        isRunning = false
                    }
                )
                AppScreen.STATS -> StatsScreen(
                    comparisonId = "CMP-20260913-001"
                )
            }
        }
    }
}

@Composable
fun HexnilTopAppBar(currentScreen: AppScreen) {
    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .background(HexnilBackground),
        color = HexnilBackground
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 20.dp, vertical = 12.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Image(
                    painter = painterResource(id = R.drawable.hexnil_logo),
                    contentDescription = "Hexnil Logo",
                    modifier = Modifier
                        .size(38.dp)
                        .clip(RoundedCornerShape(8.dp))
                        .border(1.dp, HexnilBorder, RoundedCornerShape(8.dp))
                )
                Spacer(modifier = Modifier.width(10.dp))
                Column {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(
                            text = "HEXNIL",
                            fontSize = 18.sp,
                            fontWeight = FontWeight.Black,
                            color = HexnilMainAccent,
                            letterSpacing = 1.5.sp
                        )
                        Spacer(modifier = Modifier.width(6.dp))
                        Surface(
                            shape = RoundedCornerShape(4.dp),
                            color = HexnilSecondaryCard,
                            border = BorderStroke(1.dp, HexnilBorder)
                        ) {
                            Text(
                                text = "v1.1",
                                color = HexnilAccentGlow,
                                fontSize = 10.sp,
                                fontWeight = FontWeight.Bold,
                                modifier = Modifier.padding(horizontal = 4.dp, vertical = 1.dp)
                            )
                        }
                    }
                    Text(
                        text = currentScreen.title,
                        color = HexnilSecondaryText,
                        fontSize = 11.sp
                    )
                }
            }
        }
    }
}

@Composable
fun HexnilBottomNavBar(
    currentScreen: AppScreen,
    onScreenSelected: (AppScreen) -> Unit
) {
    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .border(BorderStroke(1.dp, HexnilBorder)),
        color = HexnilCard
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 8.dp, horizontal = 12.dp),
            horizontalArrangement = Arrangement.SpaceAround,
            verticalAlignment = Alignment.CenterVertically
        ) {
            AppScreen.values().forEach { screen ->
                val isSelected = screen == currentScreen
                val textColor = if (isSelected) HexnilMainAccent else HexnilSecondaryText
                val bgColor = if (isSelected) HexnilSecondaryCard else HexnilCard

                Column(
                    modifier = Modifier
                        .clip(RoundedCornerShape(8.dp))
                        .background(bgColor)
                        .clickable { onScreenSelected(screen) }
                        .padding(horizontal = 12.dp, vertical = 6.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Text(
                        text = screen.iconSymbol,
                        fontSize = 16.sp
                    )
                    Spacer(modifier = Modifier.height(2.dp))
                    Text(
                        text = screen.tabLabel,
                        color = textColor,
                        fontSize = 10.sp,
                        fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal
                    )
                }
            }
        }
    }
}