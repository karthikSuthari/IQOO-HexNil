package com.example.iqoo_hexnil.telemetry

import android.content.Context
import android.os.Build
import android.util.Log
import java.io.File
import java.time.Instant

object TelemetryEngine {

    private const val TAG = "HexnilTelemetry"
    var lastStartupDurationMs: Long? = null

    fun getDeviceIdentity(): DeviceIdentity {
        return DeviceIdentity(
            serial = "on_device",
            manufacturer = Build.MANUFACTURER,
            model = Build.MODEL,
            androidVersion = Build.VERSION.RELEASE,
            sdk = Build.VERSION.SDK_INT,
            buildId = Build.ID,
            buildFingerprint = Build.FINGERPRINT,
            abi = Build.SUPPORTED_ABIS.firstOrNull() ?: "unknown"
        )
    }

    fun executeSession(
        context: Context,
        experimentId: String,
        workloadId: String = "startup_basic",
        iteration: Int = 1,
        action: String = "compute_work",
        operations: Int = 5000
    ): List<TelemetryRecord> {
        val device = getDeviceIdentity()
        val workload = WorkloadIdentity(id = workloadId, iteration = iteration)
        val allRecords = mutableListOf<TelemetryRecord>()

        // 1. Startup Duration Metric if recorded
        lastStartupDurationMs?.let { startupMs ->
            allRecords.add(
                TelemetryRecord(
                    experimentId = experimentId,
                    timestamp = Instant.now().toString(),
                    device = device,
                    workload = workload,
                    metric = MetricValue("app_startup_duration_ms", startupMs, "milliseconds"),
                    capability = CapabilityStatus.CONDITIONAL,
                    reason = "Measured from Activity initialization to first composition pass"
                )
            )
        }

        // 2. Pre-workload baseline telemetry
        allRecords.addAll(BatteryTelemetry.collect(context, experimentId, device, workload))
        allRecords.addAll(MemoryTelemetry.collect(context, experimentId, device, workload))
        allRecords.addAll(ThermalTelemetry.collect(context, experimentId, device, workload))
        allRecords.addAll(DisplayTelemetry.collect(context, experimentId, device, workload))
        allRecords.addAll(StorageTelemetry.collect(context, experimentId, device, workload))
        allRecords.addAll(NetworkTelemetry.collect(context, experimentId, device, workload))

        // 3. Execute deterministic workload
        val workloadResult = WorkloadRunner.execute(
            experimentId = experimentId,
            device = device,
            workloadId = workloadId,
            iteration = iteration,
            operations = operations,
            action = action
        )
        allRecords.addAll(workloadResult.records)

        // 4. Post-workload telemetry
        allRecords.addAll(BatteryTelemetry.collect(context, experimentId, device, workload))
        allRecords.addAll(MemoryTelemetry.collect(context, experimentId, device, workload))
        allRecords.addAll(ThermalTelemetry.collect(context, experimentId, device, workload))
        allRecords.addAll(DisplayTelemetry.collect(context, experimentId, device, workload))
        allRecords.addAll(StorageTelemetry.collect(context, experimentId, device, workload))

        // 5. UI Jank Metric status declaration
        allRecords.add(
            TelemetryRecord(
                experimentId = experimentId,
                timestamp = Instant.now().toString(),
                device = device,
                workload = workload,
                metric = MetricValue("ui_frame_jank_percent", null, "percent"),
                capability = CapabilityStatus.CONDITIONAL,
                reason = "In-app FrameMetrics requires continuous active window rendering; see host ADB gfxinfo for system-level frame tracking"
            )
        )

        // 6. Persist to internal app storage (accessible via run-as)
        persistRecords(context, allRecords)

        Log.i(TAG, "Completed telemetry session for $experimentId. Generated ${allRecords.size} records.")
        return allRecords
    }

    private fun persistRecords(context: Context, records: List<TelemetryRecord>) {
        try {
            // Write to internal filesDir (files/telemetry.jsonl)
            val internalFile = File(context.filesDir, "telemetry.jsonl")
            internalFile.bufferedWriter().use { writer ->
                for (r in records) {
                    writer.write(r.toJsonLine())
                    writer.newLine()
                }
            }

            // Also mirror to external files dir if available
            context.getExternalFilesDir(null)?.let { extDir ->
                val extFile = File(extDir, "telemetry.jsonl")
                extFile.bufferedWriter().use { writer ->
                    for (r in records) {
                        writer.write(r.toJsonLine())
                        writer.newLine()
                    }
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Failed to persist telemetry records to disk", e)
        }
    }
}
