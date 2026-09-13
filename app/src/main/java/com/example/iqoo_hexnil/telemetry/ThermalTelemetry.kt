package com.example.iqoo_hexnil.telemetry

import android.content.Context
import android.os.Build
import android.os.PowerManager
import java.time.Instant

object ThermalTelemetry {

    fun collect(
        context: Context,
        experimentId: String,
        device: DeviceIdentity,
        workload: WorkloadIdentity
    ): List<TelemetryRecord> {
        val records = mutableListOf<TelemetryRecord>()
        val timestamp = Instant.now().toString()

        val powerManager = context.getSystemService(Context.POWER_SERVICE) as? PowerManager

        // 1. Thermal Status (UNIVERSAL on API 29+)
        if (powerManager != null && Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            val statusInt = powerManager.currentThermalStatus
            val statusName = when (statusInt) {
                PowerManager.THERMAL_STATUS_NONE -> "NONE"
                PowerManager.THERMAL_STATUS_LIGHT -> "LIGHT"
                PowerManager.THERMAL_STATUS_MODERATE -> "MODERATE"
                PowerManager.THERMAL_STATUS_SEVERE -> "SEVERE"
                PowerManager.THERMAL_STATUS_CRITICAL -> "CRITICAL"
                PowerManager.THERMAL_STATUS_EMERGENCY -> "EMERGENCY"
                PowerManager.THERMAL_STATUS_SHUTDOWN -> "SHUTDOWN"
                else -> "UNKNOWN"
            }
            records.add(
                TelemetryRecord(
                    experimentId = experimentId,
                    timestamp = timestamp,
                    device = device,
                    workload = workload,
                    metric = MetricValue("thermal_status_name", statusName, "status"),
                    capability = CapabilityStatus.UNIVERSAL
                )
            )
            records.add(
                TelemetryRecord(
                    experimentId = experimentId,
                    timestamp = timestamp,
                    device = device,
                    workload = workload,
                    metric = MetricValue("thermal_status_level", statusInt, "level"),
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
                    metric = MetricValue("thermal_status_name", null, "status"),
                    capability = CapabilityStatus.UNSUPPORTED,
                    reason = "ThermalStatus API requires Android 10 (API 29+)"
                )
            )
        }

        // 2. Thermal Headroom (CONDITIONAL on API 30+)
        if (powerManager != null && Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            try {
                val headroom = powerManager.getThermalHeadroom(30)
                if (!headroom.isNaN() && headroom >= 0.0f) {
                    records.add(
                        TelemetryRecord(
                            experimentId = experimentId,
                            timestamp = timestamp,
                            device = device,
                            workload = workload,
                            metric = MetricValue("thermal_headroom_ratio", headroom, "ratio"),
                            capability = CapabilityStatus.CONDITIONAL
                        )
                    )
                } else {
                    records.add(
                        TelemetryRecord(
                            experimentId = experimentId,
                            timestamp = timestamp,
                            device = device,
                            workload = workload,
                            metric = MetricValue("thermal_headroom_ratio", null, "ratio"),
                            capability = CapabilityStatus.UNSUPPORTED,
                            reason = "Device thermal HAL returned NaN or does not support thermal headroom"
                        )
                    )
                }
            } catch (e: Exception) {
                records.add(
                    TelemetryRecord(
                        experimentId = experimentId,
                        timestamp = timestamp,
                        device = device,
                        workload = workload,
                        metric = MetricValue("thermal_headroom_ratio", null, "ratio"),
                        capability = CapabilityStatus.UNSUPPORTED,
                        reason = "Thermal headroom query threw: ${e.message}"
                    )
                )
            }
        } else {
            records.add(
                TelemetryRecord(
                    experimentId = experimentId,
                    timestamp = timestamp,
                    device = device,
                    workload = workload,
                    metric = MetricValue("thermal_headroom_ratio", null, "ratio"),
                    capability = CapabilityStatus.UNSUPPORTED,
                    reason = "Thermal headroom API requires Android 11 (API 30+)"
                )
            )
        }

        // 3. Raw SoC Silicon Temperature (UNSUPPORTED via public SDK)
        records.add(
            TelemetryRecord(
                experimentId = experimentId,
                timestamp = timestamp,
                device = device,
                workload = workload,
                metric = MetricValue("soc_silicon_temperature_celsius", null, "celsius"),
                capability = CapabilityStatus.UNSUPPORTED,
                reason = "Exact SoC / CPU silicon temperature is not exposed by public Android SDK without root (use host ADB thermalservice)"
            )
        )

        return records
    }
}
