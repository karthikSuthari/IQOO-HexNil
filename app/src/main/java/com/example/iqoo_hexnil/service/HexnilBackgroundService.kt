package com.example.iqoo_hexnil.service

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.IBinder
import android.os.PowerManager
import android.util.Log
import androidx.compose.runtime.mutableStateOf
import androidx.core.app.NotificationCompat
import androidx.core.app.ServiceCompat
import com.example.iqoo_hexnil.MainActivity
import com.example.iqoo_hexnil.R
import com.example.iqoo_hexnil.cloud.SupabaseSyncManager
import com.example.iqoo_hexnil.telemetry.BatteryTelemetry
import com.example.iqoo_hexnil.telemetry.DisplayTelemetry
import com.example.iqoo_hexnil.telemetry.MemoryTelemetry
import com.example.iqoo_hexnil.telemetry.NetworkTelemetry
import com.example.iqoo_hexnil.telemetry.StorageTelemetry
import com.example.iqoo_hexnil.telemetry.TelemetryEngine
import com.example.iqoo_hexnil.telemetry.ThermalTelemetry
import com.example.iqoo_hexnil.telemetry.WorkloadIdentity
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter

class HexnilBackgroundService : Service() {

    companion object {
        const val TAG = "HEXNIL_BG"
        const val CHANNEL_ID = "hexnil_background_service_channel"
        const val NOTIFICATION_ID = 40401

        const val ACTION_START = "com.example.iqoo_hexnil.action.START_BG_SERVICE"
        const val ACTION_STOP = "com.example.iqoo_hexnil.action.STOP_BG_SERVICE"

        const val PREFS_NAME = "hexnil_prefs"
        const val KEY_BG_ENABLED = "hexnil_bg_monitoring_enabled"

        // Reactive state observable by Compose UI
        val isRunning = mutableStateOf(false)
        val sampleCount = mutableStateOf(0)
        val lastSampleTime = mutableStateOf<String?>(null)
        val lastBatteryText = mutableStateOf<String?>(null)
        val lastMemoryText = mutableStateOf<String?>(null)
        val lastRefreshRateText = mutableStateOf<String?>(null)
        val lastThermalText = mutableStateOf<String?>(null)
        val lastStorageText = mutableStateOf<String?>(null)

        fun start(context: Context) {
            val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            prefs.edit().putBoolean(KEY_BG_ENABLED, true).apply()

            val intent = Intent(context, HexnilBackgroundService::class.java).apply {
                action = ACTION_START
            }
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                context.startForegroundService(intent)
            } else {
                context.startService(intent)
            }
        }

        fun stop(context: Context) {
            val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            prefs.edit().putBoolean(KEY_BG_ENABLED, false).apply()

            val intent = Intent(context, HexnilBackgroundService::class.java).apply {
                action = ACTION_STOP
            }
            context.startService(intent)
        }
    }

    private val serviceScope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private var samplingJob: Job? = null
    private var wakeLock: PowerManager.WakeLock? = null

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
        acquireWakeLock()
        Log.i(TAG, "[LIFECYCLE] HexnilBackgroundService created")
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == ACTION_STOP) {
            Log.i(TAG, "[COMMAND] Received ACTION_STOP. Stopping foreground service.")
            stopSampling()
            ServiceCompat.stopForeground(this, ServiceCompat.STOP_FOREGROUND_REMOVE)
            stopSelf()
            isRunning.value = false
            return START_NOT_STICKY
        }

        Log.i(TAG, "[COMMAND] Starting Hexnil foreground service on ${Build.MANUFACTURER} ${Build.MODEL} (Android ${Build.VERSION.RELEASE})")
        val notification = buildNotification("Monitoring active · 0 samples")

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            startForeground(
                NOTIFICATION_ID,
                notification,
                ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC
            )
        } else {
            startForeground(NOTIFICATION_ID, notification)
        }

        isRunning.value = true
        startSampling()

        return START_STICKY
    }

    private fun startSampling() {
        if (samplingJob?.isActive == true) return

        // Register device with Supabase fleet table
        serviceScope.launch {
            try {
                SupabaseSyncManager.registerDevice(this@HexnilBackgroundService)
            } catch (e: Exception) {
                Log.w(TAG, "[SUPABASE] Device registration deferred: ${e.message}")
            }
        }

        samplingJob = serviceScope.launch {
            Log.i(TAG, "[SAMPLER] Background telemetry polling loop started (interval: 15s)")
            while (isActive) {
                try {
                    sampleTelemetry()
                } catch (e: Exception) {
                    Log.e(TAG, "[SAMPLER] Error during background sampling: ${e.message}", e)
                }
                delay(15_000) // Sample every 15 seconds
            }
        }
    }

    private fun sampleTelemetry() {
        val device = TelemetryEngine.getDeviceIdentity()
        val workload = WorkloadIdentity(id = "background_monitor", iteration = sampleCount.value + 1)
        val expId = "EXP-BG-${System.currentTimeMillis() / 1000}"

        val batteryRecords = BatteryTelemetry.collect(this, expId, device, workload)
        val memoryRecords = MemoryTelemetry.collect(this, expId, device, workload)
        val thermalRecords = ThermalTelemetry.collect(this, expId, device, workload)
        val displayRecords = DisplayTelemetry.collect(this, expId, device, workload)
        val storageRecords = StorageTelemetry.collect(this, expId, device, workload)
        val networkRecords = NetworkTelemetry.collect(this, expId, device, workload)
        val allRecords = batteryRecords + memoryRecords + thermalRecords + displayRecords + storageRecords + networkRecords

        // Asynchronously stream telemetry batch to Supabase
        serviceScope.launch {
            try {
                SupabaseSyncManager.uploadTelemetryBatch(this@HexnilBackgroundService, allRecords)
            } catch (e: Exception) {
                Log.w(TAG, "[SUPABASE] Background telemetry batch skipped: ${e.message}")
            }
        }

        sampleCount.value += 1

        val formatter = DateTimeFormatter.ofPattern("HH:mm:ss").withZone(ZoneId.systemDefault())
        val timeStr = formatter.format(Instant.now())
        lastSampleTime.value = timeStr

        val batteryLevel = batteryRecords.find { it.metric.name == "battery_level_percent" }?.metric?.value?.let { "$it%" } ?: "N/A"
        val batteryState = batteryRecords.find { it.metric.name == "battery_charging_state" }?.metric?.value?.toString() ?: "discharging"
        lastBatteryText.value = "$batteryLevel ($batteryState)"

        val freeRam = memoryRecords.find { it.metric.name == "device_memory_available_mb" }?.metric?.value?.let { value ->
            val mb = (value as? Number)?.toDouble() ?: 0.0
            if (mb >= 1024.0) {
                String.format(java.util.Locale.US, "%.1f GB free", mb / 1024.0)
            } else {
                "${mb.toInt()} MB free"
            }
        } ?: "N/A"
        lastMemoryText.value = freeRam

        val refreshRate = displayRecords.find { it.metric.name == "display_refresh_rate_hz" }?.metric?.value?.let { 
            "${(it as Number).toInt()} Hz" 
        } ?: "60 Hz"
        lastRefreshRateText.value = refreshRate

        val thermalState = thermalRecords.find { it.metric.name == "thermal_status_name" }?.metric?.value?.toString() 
            ?: thermalRecords.find { it.metric.name == "thermal_status" }?.metric?.value?.toString() ?: "NORMAL"
        lastThermalText.value = thermalState

        val storageAvail = storageRecords.find { it.metric.name == "storage_available_mb" }?.metric?.value?.let { value ->
            val mb = (value as? Number)?.toDouble() ?: 0.0
            if (mb >= 1024.0) {
                String.format(java.util.Locale.US, "%.1f GB free", mb / 1024.0)
            } else {
                "${mb.toInt()} MB free"
            }
        } ?: "N/A"
        lastStorageText.value = storageAvail

        Log.i(
            TAG,
            "[SAMPLE #${sampleCount.value}] Time=$timeStr | Battery=$batteryLevel ($batteryState) | RAM=$freeRam | Display=$refreshRate | Thermal=$thermalState | Storage=$storageAvail"
        )

        // Update notification
        updateNotification("Active · ${sampleCount.value} samples ($timeStr · $refreshRate · $batteryLevel)")
    }

    private fun stopSampling() {
        samplingJob?.cancel()
        samplingJob = null
        Log.i(TAG, "[SAMPLER] Background telemetry polling stopped. Total samples: ${sampleCount.value}")
    }

    private fun acquireWakeLock() {
        try {
            val powerManager = getSystemService(Context.POWER_SERVICE) as? PowerManager
            wakeLock = powerManager?.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "Hexnil:BackgroundServiceWakeLock")
            wakeLock?.setReferenceCounted(false)
            wakeLock?.acquire(3600 * 1000L) // Safe max 1 hour timeout
        } catch (e: Exception) {
            Log.w(TAG, "Could not acquire partial wakelock: ${e.message}")
        }
    }

    private fun releaseWakeLock() {
        try {
            if (wakeLock?.isHeld == true) {
                wakeLock?.release()
            }
        } catch (e: Exception) {
            Log.w(TAG, "Could not release wakelock: ${e.message}")
        }
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "Hexnil Background Telemetry",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Monitors hardware telemetry and differential execution status in background"
                setShowBadge(false)
            }
            val manager = getSystemService(NotificationManager::class.java)
            manager?.createNotificationChannel(channel)
        }
    }

    private fun buildNotification(statusText: String): Notification {
        val launchIntent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_SINGLE_TOP
        }
        val pendingIntent = PendingIntent.getActivity(
            this,
            0,
            launchIntent,
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )

        val stopIntent = Intent(this, HexnilBackgroundService::class.java).apply {
            action = ACTION_STOP
        }
        val stopPendingIntent = PendingIntent.getService(
            this,
            1,
            stopIntent,
            PendingIntent.FLAG_IMMUTABLE
        )

        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("Hexnil Intelligence Engine")
            .setContentText(statusText)
            .setSmallIcon(R.drawable.hexnil_logo)
            .setContentIntent(pendingIntent)
            .addAction(R.drawable.hexnil_logo, "Stop", stopPendingIntent)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build()
    }

    private fun updateNotification(statusText: String) {
        val manager = getSystemService(Context.NOTIFICATION_SERVICE) as? NotificationManager
        manager?.notify(NOTIFICATION_ID, buildNotification(statusText))
    }

    override fun onDestroy() {
        super.onDestroy()
        stopSampling()
        releaseWakeLock()
        isRunning.value = false
        Log.i(TAG, "[LIFECYCLE] HexnilBackgroundService destroyed")
    }

    override fun onBind(intent: Intent?): IBinder? = null
}
