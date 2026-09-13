package com.example.iqoo_hexnil.telemetry

import android.app.ActivityManager
import android.content.Context
import java.time.Instant

object MemoryTelemetry {

    fun collect(
        context: Context,
        experimentId: String,
        device: DeviceIdentity,
        workload: WorkloadIdentity
    ): List<TelemetryRecord> {
        val records = mutableListOf<TelemetryRecord>()
        val timestamp = Instant.now().toString()

        // 1. App Process Heap Memory (UNIVERSAL)
        val runtime = Runtime.getRuntime()
        val appUsedBytes = runtime.totalMemory() - runtime.freeMemory()
        val appUsedMb = appUsedBytes / (1024.0 * 1024.0)
        val appMaxMb = runtime.maxMemory() / (1024.0 * 1024.0)

        records.add(
            TelemetryRecord(
                experimentId = experimentId,
                timestamp = timestamp,
                device = device,
                workload = workload,
                metric = MetricValue("app_heap_allocated_mb", appUsedMb, "megabytes"),
                capability = CapabilityStatus.UNIVERSAL
            )
        )
        records.add(
            TelemetryRecord(
                experimentId = experimentId,
                timestamp = timestamp,
                device = device,
                workload = workload,
                metric = MetricValue("app_heap_max_mb", appMaxMb, "megabytes"),
                capability = CapabilityStatus.UNIVERSAL
            )
        )

        // 2. Global Device RAM Memory (UNIVERSAL)
        val actManager = context.getSystemService(Context.ACTIVITY_SERVICE) as? ActivityManager
        val memInfo = ActivityManager.MemoryInfo()

        if (actManager != null) {
            actManager.getMemoryInfo(memInfo)

            val availMb = memInfo.availMem / (1024.0 * 1024.0)
            val totalMb = memInfo.totalMem / (1024.0 * 1024.0)
            val thresholdMb = memInfo.threshold / (1024.0 * 1024.0)

            records.add(
                TelemetryRecord(
                    experimentId = experimentId,
                    timestamp = timestamp,
                    device = device,
                    workload = workload,
                    metric = MetricValue("device_memory_available_mb", availMb, "megabytes"),
                    capability = CapabilityStatus.UNIVERSAL
                )
            )
            records.add(
                TelemetryRecord(
                    experimentId = experimentId,
                    timestamp = timestamp,
                    device = device,
                    workload = workload,
                    metric = MetricValue("device_memory_total_mb", totalMb, "megabytes"),
                    capability = CapabilityStatus.UNIVERSAL
                )
            )
            records.add(
                TelemetryRecord(
                    experimentId = experimentId,
                    timestamp = timestamp,
                    device = device,
                    workload = workload,
                    metric = MetricValue("device_memory_low_pressure", memInfo.lowMemory, "boolean"),
                    capability = CapabilityStatus.UNIVERSAL
                )
            )
            records.add(
                TelemetryRecord(
                    experimentId = experimentId,
                    timestamp = timestamp,
                    device = device,
                    workload = workload,
                    metric = MetricValue("device_memory_threshold_mb", thresholdMb, "megabytes"),
                    capability = CapabilityStatus.UNIVERSAL
                )
            )
        } else {
            records.add(
                TelemetryRecord(
                    experimentId = experimentId,
                    timestamp = timestamp,
                    device = device,
                    workload = workload,
                    metric = MetricValue("device_memory_available_mb", null, "megabytes"),
                    capability = CapabilityStatus.UNSUPPORTED,
                    reason = "ActivityManager service unavailable"
                )
            )
        }

        return records
    }
}
