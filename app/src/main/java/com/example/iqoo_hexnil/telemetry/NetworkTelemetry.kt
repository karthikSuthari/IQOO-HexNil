package com.example.iqoo_hexnil.telemetry

import android.content.Context
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.os.Build
import java.time.Instant

object NetworkTelemetry {

    fun collect(
        context: Context,
        experimentId: String,
        device: DeviceIdentity,
        workload: WorkloadIdentity
    ): List<TelemetryRecord> {
        val records = mutableListOf<TelemetryRecord>()
        val timestamp = Instant.now().toString()

        try {
            val cm = context.getSystemService(Context.CONNECTIVITY_SERVICE) as? ConnectivityManager
            val activeNetwork = cm?.activeNetwork
            val caps = cm?.getNetworkCapabilities(activeNetwork)

            val isWifi = caps?.hasTransport(NetworkCapabilities.TRANSPORT_WIFI) == true
            val isCellular = caps?.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR) == true
            val isMetered = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                caps?.hasCapability(NetworkCapabilities.NET_CAPABILITY_NOT_METERED) == false
            } else {
                @Suppress("DEPRECATION")
                cm?.isActiveNetworkMetered == true
            }
            val isValidated = caps?.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED) == true

            records.add(
                TelemetryRecord(
                    experimentId = experimentId,
                    timestamp = timestamp,
                    device = device,
                    workload = workload,
                    metric = MetricValue("network_type_wifi", if (isWifi) 1.0 else 0.0, "boolean"),
                    capability = CapabilityStatus.UNIVERSAL
                )
            )
            records.add(
                TelemetryRecord(
                    experimentId = experimentId,
                    timestamp = timestamp,
                    device = device,
                    workload = workload,
                    metric = MetricValue("network_type_cellular", if (isCellular) 1.0 else 0.0, "boolean"),
                    capability = CapabilityStatus.UNIVERSAL
                )
            )
            records.add(
                TelemetryRecord(
                    experimentId = experimentId,
                    timestamp = timestamp,
                    device = device,
                    workload = workload,
                    metric = MetricValue("network_is_metered", if (isMetered) 1.0 else 0.0, "boolean"),
                    capability = CapabilityStatus.UNIVERSAL
                )
            )
            records.add(
                TelemetryRecord(
                    experimentId = experimentId,
                    timestamp = timestamp,
                    device = device,
                    workload = workload,
                    metric = MetricValue("network_is_validated", if (isValidated) 1.0 else 0.0, "boolean"),
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
                    metric = MetricValue("network_type_wifi", 0.0, "boolean"),
                    capability = CapabilityStatus.CONDITIONAL,
                    reason = "Network capabilities query failed: ${e.message}"
                )
            )
        }

        return records
    }
}
