package com.example.iqoo_hexnil.cloud

import android.content.Context
import android.os.Build
import android.provider.Settings
import android.util.Log
import com.example.iqoo_hexnil.telemetry.TelemetryRecord
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL

object SupabaseSyncManager {

    private const val TAG = "HexnilSupabase"

    const val SUPABASE_URL = "https://takhdmtsdbrqucrolzfh.supabase.co"
    const val SUPABASE_ANON_KEY =
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9." +
        "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRha2hkbXRzZGJycXVjcm9semZoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODkzNTI3MzYsImV4cCI6MjEwNDkyODczNn0." +
        "JJLm6HMQZhciXq69rZYw5JGQ91d5Rhi9v-AT3qWOPL4"

    fun getDeviceId(context: Context): String {
        val androidId = Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID)
        return if (!androidId.isNullOrBlank()) {
            "android_${androidId}"
        } else {
            "${Build.MANUFACTURER}_${Build.MODEL}_${Build.ID}".replace(" ", "_")
        }
    }

    suspend fun registerDevice(context: Context): Boolean = withContext(Dispatchers.IO) {
        try {
            val deviceId = getDeviceId(context)
            val json = JSONObject().apply {
                put("device_id", deviceId)
                put("manufacturer", Build.MANUFACTURER)
                put("model", Build.MODEL)
                put("codename", Build.DEVICE)
                put("abi", Build.SUPPORTED_ABIS.firstOrNull() ?: "arm64-v8a")
                put("android_version", Build.VERSION.RELEASE)
                put("sdk_int", Build.VERSION.SDK_INT)
                put("build_id", Build.ID)
                put("build_fingerprint", Build.FINGERPRINT)
            }

            val url = URL("$SUPABASE_URL/rest/v1/devices")
            val conn = (url.openConnection() as HttpURLConnection).apply {
                requestMethod = "POST"
                setRequestProperty("apikey", SUPABASE_ANON_KEY)
                setRequestProperty("Authorization", "Bearer $SUPABASE_ANON_KEY")
                setRequestProperty("Content-Type", "application/json")
                setRequestProperty("Prefer", "resolution=merge-duplicates")
                connectTimeout = 10000
                readTimeout = 10000
                doOutput = true
            }

            OutputStreamWriter(conn.outputStream).use { writer ->
                writer.write(json.toString())
                writer.flush()
            }

            val code = conn.responseCode
            val success = code in 200..299
            Log.i(TAG, "[DEVICE] Registered device $deviceId in Supabase (HTTP $code)")
            conn.disconnect()
            success
        } catch (e: Exception) {
            Log.e(TAG, "[DEVICE] Failed to register device in Supabase: ${e.message}")
            false
        }
    }

    suspend fun uploadTelemetryBatch(
        context: Context,
        records: List<TelemetryRecord>
    ): Int = withContext(Dispatchers.IO) {
        if (records.isEmpty()) return@withContext 0

        try {
            val deviceId = getDeviceId(context)
            val jsonArray = JSONArray()

            for (r in records) {
                val obj = JSONObject().apply {
                    put("device_id", deviceId)
                    put("experiment_id", r.experimentId)
                    put("workload_id", r.workload.id)
                    put("metric_name", r.metric.name)
                    if (r.metric.value is Number) {
                        put("metric_value", (r.metric.value as Number).toDouble())
                    } else {
                        put("metric_value", JSONObject.NULL)
                    }
                    put("unit", r.metric.unit ?: JSONObject.NULL)
                    put("capability", r.capability.name)
                    put("timestamp", r.timestamp)
                }
                jsonArray.put(obj)
            }

            val url = URL("$SUPABASE_URL/rest/v1/telemetry_samples")
            val conn = (url.openConnection() as HttpURLConnection).apply {
                requestMethod = "POST"
                setRequestProperty("apikey", SUPABASE_ANON_KEY)
                setRequestProperty("Authorization", "Bearer $SUPABASE_ANON_KEY")
                setRequestProperty("Content-Type", "application/json")
                connectTimeout = 10000
                readTimeout = 10000
                doOutput = true
            }

            OutputStreamWriter(conn.outputStream).use { writer ->
                writer.write(jsonArray.toString())
                writer.flush()
            }

            val code = conn.responseCode
            val success = code in 200..299
            conn.disconnect()

            if (success) {
                Log.i(TAG, "[TELEMETRY] Successfully uploaded ${records.size} samples to Supabase")
                // Also upload wide snapshot with temp, battery, refresh rate, latency, ram, storage
                uploadTelemetrySnapshot(context, records)
                records.size
            } else {
                Log.w(TAG, "[TELEMETRY] Supabase upload failed with HTTP $code")
                0
            }
        } catch (e: Exception) {
            Log.e(TAG, "[TELEMETRY] Error uploading samples to Supabase: ${e.message}")
            0
        }
    }

    suspend fun uploadTelemetrySnapshot(
        context: Context,
        records: List<TelemetryRecord>
    ): Boolean = withContext(Dispatchers.IO) {
        if (records.isEmpty()) return@withContext false

        try {
            val deviceId = getDeviceId(context)
            val expId = records.firstOrNull()?.experimentId ?: "EXP-LIVE"
            val wid = records.firstOrNull()?.workload?.id ?: "general"

            val batteryLevel = records.find { it.metric.name == "battery_level_percent" }?.metric?.value?.let { (it as? Number)?.toDouble() }
            val batteryTemp = records.find { it.metric.name == "battery_temperature_celsius" }?.metric?.value?.let { (it as? Number)?.toDouble() }
            val batteryVolt = records.find { it.metric.name == "battery_voltage_volts" }?.metric?.value?.let { (it as? Number)?.toDouble() }
            val batteryState = records.find { it.metric.name == "battery_charging_state" }?.metric?.value?.toString()
            val thermalStatus = records.find { it.metric.name == "thermal_status_name" }?.metric?.value?.toString() 
                ?: records.find { it.metric.name == "thermal_status" }?.metric?.value?.toString()
            val thermalHeadroom = records.find { it.metric.name == "thermal_headroom_ratio" }?.metric?.value?.let { (it as? Number)?.toDouble() }
            val refreshRate = records.find { it.metric.name == "display_refresh_rate_hz" }?.metric?.value?.let { (it as? Number)?.toDouble() }
            val startupLatency = records.find { it.metric.name == "app_startup_duration_ms" }?.metric?.value?.let { (it as? Number)?.toDouble() }
            val availRam = records.find { it.metric.name == "device_memory_available_mb" }?.metric?.value?.let { (it as? Number)?.toDouble() }
            val totalRam = records.find { it.metric.name == "device_memory_total_mb" }?.metric?.value?.let { (it as? Number)?.toDouble() }
            val availStorage = records.find { it.metric.name == "storage_available_mb" }?.metric?.value?.let { (it as? Number)?.toDouble() }
            val isWifi = records.find { it.metric.name == "network_type_wifi" }?.metric?.value == 1.0
            val isCell = records.find { it.metric.name == "network_type_cellular" }?.metric?.value == 1.0
            val networkType = if (isWifi) "WIFI" else if (isCell) "CELLULAR" else "UNKNOWN"

            val snapshotObj = JSONObject().apply {
                put("device_id", deviceId)
                put("experiment_id", expId)
                put("workload_id", wid)
                batteryLevel?.let { put("battery_level_percent", it) }
                batteryTemp?.let { put("battery_temperature_celsius", it) }
                batteryVolt?.let { put("battery_voltage_volts", it) }
                batteryState?.let { put("battery_charging_state", it) }
                thermalStatus?.let { put("thermal_status", it) }
                thermalHeadroom?.let { put("thermal_headroom", it) }
                refreshRate?.let { put("display_refresh_rate_hz", it) }
                startupLatency?.let { put("app_startup_latency_ms", it) }
                availRam?.let { put("available_ram_mb", it) }
                totalRam?.let { put("total_ram_mb", it) }
                availStorage?.let { put("storage_available_mb", it) }
                put("network_type", networkType)
            }

            val url = URL("$SUPABASE_URL/rest/v1/device_telemetry_snapshots")
            val conn = (url.openConnection() as HttpURLConnection).apply {
                requestMethod = "POST"
                setRequestProperty("apikey", SUPABASE_ANON_KEY)
                setRequestProperty("Authorization", "Bearer $SUPABASE_ANON_KEY")
                setRequestProperty("Content-Type", "application/json")
                setRequestProperty("Prefer", "resolution=merge-duplicates")
                connectTimeout = 10000
                readTimeout = 10000
                doOutput = true
            }

            OutputStreamWriter(conn.outputStream).use { writer ->
                writer.write(snapshotObj.toString())
                writer.flush()
            }

            val code = conn.responseCode
            val success = code in 200..299
            conn.disconnect()
            if (success) {
                Log.i(TAG, "[SNAPSHOT] Posted wide telemetry snapshot to Supabase (HTTP $code)")
            }
            success
        } catch (e: Exception) {
            Log.e(TAG, "[SNAPSHOT] Error posting telemetry snapshot: ${e.message}")
            false
        }
    }

    suspend fun fetchLatestDeviceReport(context: Context): JSONObject? = withContext(Dispatchers.IO) {
        try {
            val deviceId = getDeviceId(context)
            val url = URL("$SUPABASE_URL/rest/v1/device_reports?device_id=eq.$deviceId&select=*&order=updated_at.desc&limit=1")
            val conn = (url.openConnection() as HttpURLConnection).apply {
                requestMethod = "GET"
                setRequestProperty("apikey", SUPABASE_ANON_KEY)
                setRequestProperty("Authorization", "Bearer $SUPABASE_ANON_KEY")
                connectTimeout = 10000
                readTimeout = 10000
            }

            if (conn.responseCode in 200..299) {
                val response = BufferedReader(InputStreamReader(conn.inputStream)).use { it.readText() }
                val jsonArray = JSONArray(response)
                conn.disconnect()
                if (jsonArray.length() > 0) {
                    return@withContext jsonArray.getJSONObject(0)
                }
            } else {
                conn.disconnect()
            }
            null
        } catch (e: Exception) {
            Log.e(TAG, "[REPORT] Error fetching device report: ${e.message}")
            null
        }
    }

    suspend fun fetchDeviceIssues(context: Context): JSONArray? = withContext(Dispatchers.IO) {
        try {
            val deviceId = getDeviceId(context)
            val url = URL("$SUPABASE_URL/rest/v1/issue_classifications?device_id=eq.$deviceId&select=*&order=created_at.desc")
            val conn = (url.openConnection() as HttpURLConnection).apply {
                requestMethod = "GET"
                setRequestProperty("apikey", SUPABASE_ANON_KEY)
                setRequestProperty("Authorization", "Bearer $SUPABASE_ANON_KEY")
                connectTimeout = 10000
                readTimeout = 10000
            }

            if (conn.responseCode in 200..299) {
                val response = BufferedReader(InputStreamReader(conn.inputStream)).use { it.readText() }
                conn.disconnect()
                return@withContext JSONArray(response)
            } else {
                conn.disconnect()
            }
            null
        } catch (e: Exception) {
            Log.e(TAG, "[ISSUES] Error fetching device issues: ${e.message}")
            null
        }
    }
}
