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
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.launch
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
import com.example.iqoo_hexnil.service.HexnilBackgroundService
import com.example.iqoo_hexnil.telemetry.TelemetryEngine
import com.example.iqoo_hexnil.telemetry.TelemetryRecord
import com.example.iqoo_hexnil.ui.AiExplanationScreen
import com.example.iqoo_hexnil.ui.AppDestination
import com.example.iqoo_hexnil.ui.AwaitingUpdateScreen
import com.example.iqoo_hexnil.ui.BottomTab
import com.example.iqoo_hexnil.ui.ClaimsScreen
import com.example.iqoo_hexnil.ui.DeviceScreen
import com.example.iqoo_hexnil.ui.ExperimentDetailScreen
import com.example.iqoo_hexnil.ui.FinalEvidenceReportScreen
import com.example.iqoo_hexnil.ui.MetricDetailScreen
import com.example.iqoo_hexnil.ui.MonitorScreen
import com.example.iqoo_hexnil.ui.OverviewScreen
import com.example.iqoo_hexnil.ui.ResultsScreen
import com.example.iqoo_hexnil.ui.SettingsAboutScreen
import com.example.iqoo_hexnil.ui.UpdateDetectedScreen
import com.example.iqoo_hexnil.ui.UpdatesScreen
import com.example.iqoo_hexnil.ui.V0BaselineScreen
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
        Log.i(TAG, "[INIT] Hexnil OS Update Impact Intelligence Platform Started")
        Log.i(TAG, "[INIT] Target Device: ${Build.MANUFACTURER} ${Build.MODEL} (Android ${Build.VERSION.RELEASE}, SDK ${Build.VERSION.SDK_INT})")
        Log.i(TAG, "==================================================")

        handleIncomingIntent(intent)

        // Resume persistent background monitoring if previously enabled
        val prefs = getSharedPreferences(HexnilBackgroundService.PREFS_NAME, MODE_PRIVATE)
        val bgEnabled = prefs.getBoolean(HexnilBackgroundService.KEY_BG_ENABLED, false)
        if (bgEnabled && !HexnilBackgroundService.isRunning.value) {
            Log.i(TAG, "[INIT] Resuming persistent background service")
            HexnilBackgroundService.start(this)
        }

        // Sync with Supabase cloud on app startup
        lifecycleScope.launch {
            HexnilRepository.syncWithSupabase(this@MainActivity)
        }

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
                        lifecycleScope.launch {
                            com.example.iqoo_hexnil.cloud.SupabaseSyncManager.uploadTelemetryBatch(this@MainActivity, records)
                        }
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
            val records = TelemetryEngine.executeSession(
                context = this,
                experimentId = expId,
                workloadId = workloadId,
                iteration = iteration,
                action = action,
                operations = operations
            )
            lifecycleScope.launch {
                com.example.iqoo_hexnil.cloud.SupabaseSyncManager.uploadTelemetryBatch(this@MainActivity, records)
            }
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
                is AppDestination.Monitor -> selectedBottomTab = BottomTab.MONITOR
                is AppDestination.Updates -> selectedBottomTab = BottomTab.UPDATES
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
            BottomTab.MONITOR -> AppDestination.Monitor
            BottomTab.UPDATES -> AppDestination.Updates
            BottomTab.RESULTS -> AppDestination.Results
            BottomTab.DEVICE -> AppDestination.Device
        }
    }

    // Handle system back button
    BackHandler(enabled = backStack.isNotEmpty()) {
        navigateBack()
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
                    onNavigateToMonitor = { selectBottomTab(BottomTab.MONITOR) },
                    onNavigateToUpdates = { selectBottomTab(BottomTab.UPDATES) },
                    onNavigateToResults = { selectBottomTab(BottomTab.RESULTS) },
                    onNavigateToDevice = { selectBottomTab(BottomTab.DEVICE) },
                    onNavigateToComparison = { navigateTo(AppDestination.V0V1Comparison) },
                    onNavigateToReport = { navigateTo(AppDestination.FinalEvidenceReport) },
                    onNavigateToMetricDetail = { metricKey ->
                        navigateTo(AppDestination.MetricDetail(metricKey))
                    }
                )

                is AppDestination.Monitor -> MonitorScreen(
                    device = deviceInfo,
                    onNavigateToBaseline = { navigateTo(AppDestination.V0Baseline) }
                )

                is AppDestination.Updates -> UpdatesScreen(
                    onNavigateToComparison = { navigateTo(AppDestination.V0V1Comparison) },
                    onNavigateToAwaitingUpdate = { navigateTo(AppDestination.AwaitingUpdate) },
                    onNavigateToUpdateDetected = { navigateTo(AppDestination.UpdateDetected) }
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

                is AppDestination.V0Baseline -> V0BaselineScreen(
                    onNavigateToClaims = { navigateTo(AppDestination.Claims) }
                )

                is AppDestination.AwaitingUpdate -> AwaitingUpdateScreen()

                is AppDestination.UpdateDetected -> UpdateDetectedScreen(
                    onProceedToValidation = { navigateTo(AppDestination.Validation) }
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

                is AppDestination.IssueClassification -> ResultsScreen(
                    analysis = analysis,
                    onNavigateToMetricDetail = { metricKey ->
                        navigateTo(AppDestination.MetricDetail(metricKey))
                    }
                )

                is AppDestination.PredictionEvaluation -> ResultsScreen(
                    analysis = analysis,
                    onNavigateToMetricDetail = { metricKey ->
                        navigateTo(AppDestination.MetricDetail(metricKey))
                    }
                )

                is AppDestination.FinalEvidenceReport -> FinalEvidenceReportScreen()

                is AppDestination.AiExplanation -> AiExplanationScreen(
                    analysis = analysis
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

                is AppDestination.Claims -> ClaimsScreen(
                    claims = claims
                )

                is AppDestination.ExperimentDetail -> ExperimentDetailScreen(
                    analysis = analysis
                )

                is AppDestination.SettingsAbout -> SettingsAboutScreen()
            }
        }
    }
}