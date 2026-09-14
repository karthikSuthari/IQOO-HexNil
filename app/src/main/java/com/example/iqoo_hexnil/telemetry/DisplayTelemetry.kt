package com.example.iqoo_hexnil.telemetry

import android.content.Context
import android.os.Build
import android.view.WindowManager
import java.time.Instant

object DisplayTelemetry {

    fun collect(
        context: Context,
        experimentId: String,
        device: DeviceIdentity,
        workload: WorkloadIdentity
    ): List<TelemetryRecord> {
        val records = mutableListOf<TelemetryRecord>()
        val timestamp = Instant.now().toString()

        try {
            val wm = context.getSystemService(Context.WINDOW_SERVICE) as? WindowManager
            val display = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                try {
                    context.display
                } catch (e: Exception) {
                    @Suppress("DEPRECATION")
                    wm?.defaultDisplay
                }
            } else {
                @Suppress("DEPRECATION")
                wm?.defaultDisplay
            }

            // 1. Display Refresh Rate in Hz
            @Suppress("DEPRECATION")
            val refreshRate = display?.mode?.refreshRate ?: display?.refreshRate ?: 60.0f
            records.add(
                TelemetryRecord(
                    experimentId = experimentId,
                    timestamp = timestamp,
                    device = device,
                    workload = workload,
                    metric = MetricValue("display_refresh_rate_hz", refreshRate.toDouble(), "hertz"),
                    capability = CapabilityStatus.UNIVERSAL
                )
            )

            // 2. Display Resolution & Density
            val metrics = context.resources.displayMetrics
            records.add(
                TelemetryRecord(
                    experimentId = experimentId,
                    timestamp = timestamp,
                    device = device,
                    workload = workload,
                    metric = MetricValue("display_width_pixels", metrics.widthPixels.toDouble(), "pixels"),
                    capability = CapabilityStatus.UNIVERSAL
                )
            )
            records.add(
                TelemetryRecord(
                    experimentId = experimentId,
                    timestamp = timestamp,
                    device = device,
                    workload = workload,
                    metric = MetricValue("display_height_pixels", metrics.heightPixels.toDouble(), "pixels"),
                    capability = CapabilityStatus.UNIVERSAL
                )
            )
            records.add(
                TelemetryRecord(
                    experimentId = experimentId,
                    timestamp = timestamp,
                    device = device,
                    workload = workload,
                    metric = MetricValue("display_density_dpi", metrics.densityDpi.toDouble(), "dpi"),
                    capability = CapabilityStatus.UNIVERSAL
                )
            )

            // 3. Display HDR Capability
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                val isHdr = display?.isHdr == true
                records.add(
                    TelemetryRecord(
                        experimentId = experimentId,
                        timestamp = timestamp,
                        device = device,
                        workload = workload,
                        metric = MetricValue("display_hdr_capable", if (isHdr) 1.0 else 0.0, "boolean"),
                        capability = CapabilityStatus.CONDITIONAL
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
                    metric = MetricValue("display_refresh_rate_hz", 60.0, "hertz"),
                    capability = CapabilityStatus.CONDITIONAL,
                    reason = "Failed to query display properties: ${e.message}"
                )
            )
        }

        return records
    }
}
