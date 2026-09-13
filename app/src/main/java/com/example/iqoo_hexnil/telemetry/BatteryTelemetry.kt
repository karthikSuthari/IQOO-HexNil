package com.example.iqoo_hexnil.telemetry

import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.BatteryManager
import java.time.Instant

object BatteryTelemetry {

    fun collect(
        context: Context,
        experimentId: String,
        device: DeviceIdentity,
        workload: WorkloadIdentity
    ): List<TelemetryRecord> {
        val records = mutableListOf<TelemetryRecord>()
        val timestamp = Instant.now().toString()

        val ifilter = IntentFilter(Intent.ACTION_BATTERY_CHANGED)
        val batteryStatus: Intent? = context.registerReceiver(null, ifilter)

        // 1. Battery Level (UNIVERSAL)
        val level: Int = batteryStatus?.getIntExtra(BatteryManager.EXTRA_LEVEL, -1) ?: -1
        val scale: Int = batteryStatus?.getIntExtra(BatteryManager.EXTRA_SCALE, -1) ?: -1
        if (level >= 0 && scale > 0) {
            val batteryPct = (level / scale.toFloat()) * 100.0f
            records.add(
                TelemetryRecord(
                    experimentId = experimentId,
                    timestamp = timestamp,
                    device = device,
                    workload = workload,
                    metric = MetricValue("battery_level_percent", batteryPct, "percent"),
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
                    metric = MetricValue("battery_level_percent", null, "percent"),
                    capability = CapabilityStatus.UNSUPPORTED,
                    reason = "Battery level not reported by system broadcast"
                )
            )
        }

        // 2. Charging State (UNIVERSAL)
        val status: Int = batteryStatus?.getIntExtra(BatteryManager.EXTRA_STATUS, -1) ?: -1
        val statusString = when (status) {
            BatteryManager.BATTERY_STATUS_CHARGING -> "CHARGING"
            BatteryManager.BATTERY_STATUS_DISCHARGING -> "DISCHARGING"
            BatteryManager.BATTERY_STATUS_FULL -> "FULL"
            BatteryManager.BATTERY_STATUS_NOT_CHARGING -> "NOT_CHARGING"
            else -> "UNKNOWN"
        }
        records.add(
            TelemetryRecord(
                experimentId = experimentId,
                timestamp = timestamp,
                device = device,
                workload = workload,
                metric = MetricValue("battery_charging_state", statusString, "state"),
                capability = CapabilityStatus.UNIVERSAL
            )
        )

        // 3. Battery Temperature (CONDITIONAL)
        val rawTemp = batteryStatus?.getIntExtra(BatteryManager.EXTRA_TEMPERATURE, -1) ?: -1
        if (rawTemp > 0) {
            val tempCelsius = rawTemp / 10.0f
            records.add(
                TelemetryRecord(
                    experimentId = experimentId,
                    timestamp = timestamp,
                    device = device,
                    workload = workload,
                    metric = MetricValue("battery_temperature_celsius", tempCelsius, "celsius"),
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
                    metric = MetricValue("battery_temperature_celsius", null, "celsius"),
                    capability = CapabilityStatus.UNSUPPORTED,
                    reason = "Battery temperature sensor not exposed in broadcast"
                )
            )
        }

        // 4. Battery Voltage (CONDITIONAL)
        val rawVoltage = batteryStatus?.getIntExtra(BatteryManager.EXTRA_VOLTAGE, -1) ?: -1
        if (rawVoltage > 0) {
            val voltageVolts = rawVoltage / 1000.0f
            records.add(
                TelemetryRecord(
                    experimentId = experimentId,
                    timestamp = timestamp,
                    device = device,
                    workload = workload,
                    metric = MetricValue("battery_voltage_volts", voltageVolts, "volts"),
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
                    metric = MetricValue("battery_voltage_volts", null, "volts"),
                    capability = CapabilityStatus.UNSUPPORTED,
                    reason = "Battery voltage not exposed"
                )
            )
        }

        // 5. Battery Current Now (CONDITIONAL)
        val bm = context.getSystemService(Context.BATTERY_SERVICE) as? BatteryManager
        val currentUa = bm?.getIntProperty(BatteryManager.BATTERY_PROPERTY_CURRENT_NOW)
        if (currentUa != null && currentUa != Int.MIN_VALUE && currentUa != 0) {
            records.add(
                TelemetryRecord(
                    experimentId = experimentId,
                    timestamp = timestamp,
                    device = device,
                    workload = workload,
                    metric = MetricValue("battery_current_microamps", currentUa, "microamps"),
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
                    metric = MetricValue("battery_current_microamps", null, "microamps"),
                    capability = CapabilityStatus.UNSUPPORTED,
                    reason = "Direct current measurement property not supported by device fuel gauge HAL"
                )
            )
        }

        return records
    }
}
