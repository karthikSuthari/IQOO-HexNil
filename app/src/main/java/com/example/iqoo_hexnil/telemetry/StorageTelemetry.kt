package com.example.iqoo_hexnil.telemetry

import android.content.Context
import android.os.Environment
import android.os.StatFs
import java.time.Instant

object StorageTelemetry {

    fun collect(
        context: Context,
        experimentId: String,
        device: DeviceIdentity,
        workload: WorkloadIdentity
    ): List<TelemetryRecord> {
        val records = mutableListOf<TelemetryRecord>()
        val timestamp = Instant.now().toString()

        try {
            val statFs = StatFs(Environment.getDataDirectory().path)
            val blockSize = statFs.blockSizeLong
            val totalBlocks = statFs.blockCountLong
            val availableBlocks = statFs.availableBlocksLong

            val totalBytes = totalBlocks * blockSize
            val availableBytes = availableBlocks * blockSize
            val usedBytes = totalBytes - availableBytes

            val totalMb = totalBytes / (1024.0 * 1024.0)
            val availableMb = availableBytes / (1024.0 * 1024.0)
            val usedPercent = if (totalBytes > 0) (usedBytes.toDouble() / totalBytes.toDouble()) * 100.0 else 0.0

            records.add(
                TelemetryRecord(
                    experimentId = experimentId,
                    timestamp = timestamp,
                    device = device,
                    workload = workload,
                    metric = MetricValue("storage_available_mb", availableMb, "megabytes"),
                    capability = CapabilityStatus.UNIVERSAL
                )
            )
            records.add(
                TelemetryRecord(
                    experimentId = experimentId,
                    timestamp = timestamp,
                    device = device,
                    workload = workload,
                    metric = MetricValue("storage_total_mb", totalMb, "megabytes"),
                    capability = CapabilityStatus.UNIVERSAL
                )
            )
            records.add(
                TelemetryRecord(
                    experimentId = experimentId,
                    timestamp = timestamp,
                    device = device,
                    workload = workload,
                    metric = MetricValue("storage_used_percent", usedPercent, "percent"),
                    capability = CapabilityStatus.UNIVERSAL
                )
            )
        } catch (e: Exception) {
            records.add(
                TelemetryRecord(
                    experimentId = experimentId,
                    timestamp = timestamp,
                    device = device,
                    workload = workload,
                    metric = MetricValue("storage_available_mb", null, "megabytes"),
                    capability = CapabilityStatus.UNSUPPORTED,
                    reason = "Storage StatFs query failed: ${e.message}"
                )
            )
        }

        return records
    }
}
