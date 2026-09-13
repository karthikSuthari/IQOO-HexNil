package com.example.iqoo_hexnil.telemetry

import android.os.SystemClock
import java.security.MessageDigest
import java.time.Instant

data class WorkloadResult(
    val workloadId: String,
    val iteration: Int,
    val startTimestamp: String,
    val endTimestamp: String,
    val durationMs: Long,
    val success: Boolean,
    val operationsCount: Int,
    val records: List<TelemetryRecord>
)

object WorkloadRunner {

    fun execute(
        experimentId: String,
        device: DeviceIdentity,
        workloadId: String = "startup_basic",
        iteration: Int = 1,
        operations: Int = 5000
    ): WorkloadResult {
        val workload = WorkloadIdentity(id = workloadId, iteration = iteration)
        val startInstant = Instant.now()
        val startMillis = SystemClock.elapsedRealtime()

        var success = true
        try {
            // Deterministic compute workload: repeatable SHA-256 hashing over fixed seed
            val digest = MessageDigest.getInstance("SHA-256")
            var data = "HexnilPhase2SeedPayload_$workloadId".toByteArray(Charsets.UTF_8)
            for (i in 0 until operations) {
                digest.update(data)
                data = digest.digest()
            }
        } catch (e: Exception) {
            success = false
        }

        val endMillis = SystemClock.elapsedRealtime()
        val endInstant = Instant.now()
        val durationMs = endMillis - startMillis

        val records = mutableListOf<TelemetryRecord>()

        // 1. Workload Duration (UNIVERSAL)
        records.add(
            TelemetryRecord(
                experimentId = experimentId,
                timestamp = endInstant.toString(),
                device = device,
                workload = workload,
                metric = MetricValue("workload_duration_ms", durationMs, "milliseconds"),
                capability = CapabilityStatus.UNIVERSAL
            )
        )

        // 2. Workload Success Flag (UNIVERSAL)
        records.add(
            TelemetryRecord(
                experimentId = experimentId,
                timestamp = endInstant.toString(),
                device = device,
                workload = workload,
                metric = MetricValue("workload_success", success, "boolean"),
                capability = CapabilityStatus.UNIVERSAL
            )
        )

        // 3. Workload Operations Count (UNIVERSAL)
        records.add(
            TelemetryRecord(
                experimentId = experimentId,
                timestamp = endInstant.toString(),
                device = device,
                workload = workload,
                metric = MetricValue("workload_operations_count", operations, "operations"),
                capability = CapabilityStatus.UNIVERSAL
            )
        )

        // 4. CPU Available Processors (UNIVERSAL)
        val processors = Runtime.getRuntime().availableProcessors()
        records.add(
            TelemetryRecord(
                experimentId = experimentId,
                timestamp = endInstant.toString(),
                device = device,
                workload = workload,
                metric = MetricValue("cpu_available_processors", processors, "cores"),
                capability = CapabilityStatus.UNIVERSAL
            )
        )

        // 5. Raw CPU Utilization Percent (UNSUPPORTED via public SDK)
        records.add(
            TelemetryRecord(
                experimentId = experimentId,
                timestamp = endInstant.toString(),
                device = device,
                workload = workload,
                metric = MetricValue("cpu_utilization_percent", null, "percent"),
                capability = CapabilityStatus.UNSUPPORTED,
                reason = "Android restricted /proc/stat access in API 26+ for application sandboxes"
            )
        )

        return WorkloadResult(
            workloadId = workloadId,
            iteration = iteration,
            startTimestamp = startInstant.toString(),
            endTimestamp = endInstant.toString(),
            durationMs = durationMs,
            success = success,
            operationsCount = operations,
            records = records
        )
    }
}
