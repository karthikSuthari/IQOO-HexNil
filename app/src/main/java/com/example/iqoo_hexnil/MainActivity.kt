package com.example.iqoo_hexnil

import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.os.SystemClock
import android.util.Log
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import com.example.iqoo_hexnil.data.HexnilRepository
import com.example.iqoo_hexnil.telemetry.TelemetryEngine
import com.example.iqoo_hexnil.telemetry.TelemetryRecord
import com.example.iqoo_hexnil.ui.AiExplanationScreen
import com.example.iqoo_hexnil.ui.AppDestination
import com.example.iqoo_hexnil.ui.BottomTab
import com.example.iqoo_hexnil.ui.ClaimsScreen
import com.example.iqoo_hexnil.ui.DeviceScreen
import com.example.iqoo_hexnil.ui.ExperimentDetailScreen
import com.example.iqoo_hexnil.ui.MetricDetailScreen
import com.example.iqoo_hexnil.ui.OverviewScreen
import com.example.iqoo_hexnil.ui.ResultsScreen
import com.example.iqoo_hexnil.ui.SettingsAboutScreen
import com.example.iqoo_hexnil.ui.V0V1ComparisonScreen
import com.example.iqoo_hexnil.ui.ValidationScreen
import com.example.iqoo_hexnil.ui.components.HexnilBottomBar
import com.example.iqoo_hexnil.ui.components.HexnilTopBar
import com.example.iqoo_hexnil.ui.theme.HexnilBackground
import com.example.iqoo_hexnil.ui.theme.IQOOHEXNILTheme

private const val TAG = "HEXNIL"

class MainActivity : ComponentActivity() {

    private val activityCreateTime = SystemClock.elapsedRealtime()
    private var pendingExperimentId: String? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        Log.i(TAG, "==================================================")
        Log.i(TAG, "[INIT] Hexnil Companion App Engine Started")
        Log.i(TAG, "[INIT] Target Device: ${Build.MANUFACTURER} ${Build.MODEL} (Android ${Build.VERSION.RELEASE}, SDK ${Build.VERSION.SDK_INT})")
        Log.i(TAG, "==================================================")

        handleIncomingIntent(intent)

        setContent {
            IQOOHEXNILTheme {
                HexnilCompanionApp(
                    activityCreateTime = activityCreateTime,
                    initialExperimentId = pendingExperimentId,
                    onExecuteSession = { expId, wid, action, ops ->
                        Log.i(TAG, "[WORKLOAD] Executing session: $wid ($action, ops=$ops, exp=$expId)")
                        val records = TelemetryEngine.executeSession(
                            context = this@MainActivity,
                            experimentId = expId,
                            workloadId = wid,
                            action = action,
                            operations = ops
                        )
                        Log.i(TAG, "[WORKLOAD] Completed session $wid. Generated ${records.size} telemetry records.")
                        records
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
fun HexnilCompanionApp(
    activityCreateTime: Long,
    initialExperimentId: String?,
    onExecuteSession: (String, String, String, Int) -> List<TelemetryRecord>
) {
    val context = LocalContext.current
    val analysis = remember { HexnilRepository.getComparisonAnalysis() }
    val workloads = remember { HexnilRepository.getWorkloads() }
    val claims = remember { HexnilRepository.getReleaseClaims() }
    val deviceInfo = remember { HexnilRepository.getDeviceHardwareInfo(context) }

    var selectedBottomTab by remember { mutableStateOf(BottomTab.OVERVIEW) }
    var currentDestination by remember { mutableStateOf<AppDestination>(AppDestination.Overview) }
    var backStack by remember { mutableStateOf<List<AppDestination>>(emptyList()) }

    var telemetryRecords by remember { mutableStateOf<List<TelemetryRecord>>(emptyList()) }
    var isRunningWorkload by remember { mutableStateOf(false) }

    fun navigateTo(destination: AppDestination) {
        backStack = backStack + currentDestination
        currentDestination = destination
    }

    fun navigateBack() {
        if (backStack.isNotEmpty()) {
            val previous = backStack.last()
            backStack = backStack.dropLast(1)
            currentDestination = previous
            // Synchronize bottom tab if root
            when (previous) {
                is AppDestination.Overview -> selectedBottomTab = BottomTab.OVERVIEW
                is AppDestination.Validation -> selectedBottomTab = BottomTab.VALIDATION
                is AppDestination.Results -> selectedBottomTab = BottomTab.RESULTS
                is AppDestination.Device -> selectedBottomTab = BottomTab.DEVICE
                else -> {}
            }
        }
    }

    fun selectBottomTab(tab: BottomTab) {
        selectedBottomTab = tab
        backStack = emptyList() // reset stack on tab switch
        currentDestination = when (tab) {
            BottomTab.OVERVIEW -> AppDestination.Overview
            BottomTab.VALIDATION -> AppDestination.Validation
            BottomTab.RESULTS -> AppDestination.Results
            BottomTab.DEVICE -> AppDestination.Device
        }
    }

    // Handle system back button
    BackHandler(enabled = backStack.isNotEmpty()) {
        navigateBack()
    }

    LaunchedEffect(Unit) {
        Log.i(TAG, "[HEXNIL_DATA] Loading baseline and update comparison...")
        Log.i(TAG, "[HEXNIL_DATA] Analysis ID: ${analysis.analysisId}")
        Log.i(TAG, "[HEXNIL_DATA] Comparison: ${analysis.v0ExperimentId} -> ${analysis.v1ExperimentId}")
        Log.i(TAG, "[HEXNIL_DATA] Metrics: ${analysis.metricsAnalyzed} analyzed | 0 Regressions | ${analysis.metricsUnchanged} Unchanged | ${analysis.metricsInconclusive} Inconclusive")
        Log.i(TAG, "[HEXNIL_DATA] Loaded ${workloads.size} declarative benchmark workloads")
        workloads.forEach { wl ->
            Log.i(TAG, "  -> Workload: ${wl.id} (${wl.name}) | Priority: ${wl.priority.label} | Status: ${wl.status.name}")
        }
        Log.i(TAG, "[HEXNIL_DATA] Loaded ${claims.size} OEM release claims")
        claims.forEach { clm ->
            Log.i(TAG, "  -> Claim: ${clm.id} (${clm.title}) | Risk: ${clm.riskLevel.label} | Status: ${clm.validationStatus}")
        }
    }

    LaunchedEffect(selectedBottomTab) {
        Log.i(TAG, "[NAV] Active Bottom Navigation Tab: ${selectedBottomTab.name}")
    }

    LaunchedEffect(currentDestination) {
        Log.i(TAG, "[NAV] Destination changed to: ${currentDestination::class.simpleName}")
    }

    // Capture bootstrap telemetry on cold start
    LaunchedEffect(Unit) {
        val startupDuration = SystemClock.elapsedRealtime() - activityCreateTime
        TelemetryEngine.lastStartupDurationMs = startupDuration
        telemetryRecords = onExecuteSession(
            initialExperimentId ?: analysis.v0ExperimentId,
            "startup_basic",
            "launch_app",
            1
        )
    }

    Scaffold(
        modifier = Modifier.fillMaxSize(),
        containerColor = HexnilBackground,
        topBar = {
            HexnilTopBar(
                screenTitle = currentDestination.title,
                canNavigateBack = backStack.isNotEmpty(),
                onNavigateBack = { navigateBack() },
                onOpenSettings = {
                    if (currentDestination != AppDestination.SettingsAbout) {
                        navigateTo(AppDestination.SettingsAbout)
                    }
                }
            )
        },
        bottomBar = {
            HexnilBottomBar(
                selectedTab = selectedBottomTab,
                onTabSelected = { selectBottomTab(it) }
            )
        }
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
        ) {
            when (val dest = currentDestination) {
                is AppDestination.Overview -> OverviewScreen(
                    analysis = analysis,
                    device = deviceInfo,
                    onNavigateToResults = { selectBottomTab(BottomTab.RESULTS) },
                    onNavigateToClaims = { navigateTo(AppDestination.Claims) },
                    onNavigateToValidation = { selectBottomTab(BottomTab.VALIDATION) },
                    onNavigateToComparison = { navigateTo(AppDestination.V0V1Comparison) },
                    onNavigateToProvenance = { navigateTo(AppDestination.ExperimentDetail) },
                    onNavigateToAiExplanation = { navigateTo(AppDestination.AiExplanation) },
                    onNavigateToMetricDetail = { metricKey ->
                        navigateTo(AppDestination.MetricDetail(metricKey))
                    }
                )

                is AppDestination.Validation -> ValidationScreen(
                    workloads = workloads,
                    onRunWorkloadAction = { wid, action ->
                        Log.i(TAG, "[WORKLOAD] User triggered execution for: $wid ($action)")
                        isRunningWorkload = true
                        telemetryRecords = onExecuteSession(analysis.v1ExperimentId, wid, action, 5000)
                        isRunningWorkload = false
                    }
                )

                is AppDestination.Results -> ResultsScreen(
                    analysis = analysis,
                    onNavigateToMetricDetail = { metricKey ->
                        Log.i(TAG, "[DRILLDOWN] Viewing metric detail for: $metricKey")
                        navigateTo(AppDestination.MetricDetail(metricKey))
                    }
                )

                is AppDestination.Device -> DeviceScreen(
                    device = deviceInfo,
                    records = telemetryRecords,
                    isRunning = isRunningWorkload,
                    onCollectSnapshot = {
                        Log.i(TAG, "[TELEMETRY] User requested live sensor capture snapshot")
                        isRunningWorkload = true
                        telemetryRecords = onExecuteSession(analysis.v1ExperimentId, "snapshot", "collect_snapshot", 1)
                        isRunningWorkload = false
                    }
                )

                is AppDestination.Claims -> ClaimsScreen(
                    claims = claims
                )

                is AppDestination.V0V1Comparison -> V0V1ComparisonScreen(
                    analysis = analysis
                )

                is AppDestination.MetricDetail -> {
                    val selectedMetric = analysis.metricResults.find { it.key == dest.metricKey }
                        ?: analysis.metricResults.first()
                    MetricDetailScreen(
                        metric = selectedMetric
                    )
                }

                is AppDestination.ExperimentDetail -> ExperimentDetailScreen(
                    analysis = analysis
                )

                is AppDestination.AiExplanation -> AiExplanationScreen(
                    analysis = analysis
                )

                is AppDestination.SettingsAbout -> SettingsAboutScreen()
            }
        }
    }
}