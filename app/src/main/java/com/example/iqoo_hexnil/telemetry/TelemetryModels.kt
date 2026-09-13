package com.example.iqoo_hexnil.telemetry

import org.json.JSONObject

enum class CapabilityStatus {
    UNIVERSAL,
    CONDITIONAL,
    UNSUPPORTED
}

data class MetricValue(
    val name: String,
    val value: Any? = null,
    val unit: String? = null
)

data class WorkloadIdentity(
    val id: String = "startup_basic",
    val iteration: Int = 1
)

data class SoftwareIdentity(
    val packageName: String = "com.example.iqoo_hexnil",
    val versionName: String? = "1.0",
    val versionCode: Int? = 1
)

data class DeviceIdentity(
    val serial: String,
    val manufacturer: String,
    val model: String,
    val androidVersion: String,
    val sdk: Int,
    val buildId: String,
    val buildFingerprint: String,
    val abi: String
)

data class TelemetryRecord(
    val experimentId: String,
    val timestamp: String,
    val device: DeviceIdentity,
    val software: SoftwareIdentity = SoftwareIdentity(),
    val workload: WorkloadIdentity = WorkloadIdentity(),
    val metric: MetricValue,
    val source: String = "android_app",
    val capability: CapabilityStatus,
    val reason: String? = null
) {
    fun toJson(): JSONObject {
        val json = JSONObject()
        json.put("experiment_id", experimentId)
        json.put("timestamp", timestamp)

        val devJson = JSONObject()
        devJson.put("serial", device.serial)
        devJson.put("manufacturer", device.manufacturer)
        devJson.put("model", device.model)
        devJson.put("android_version", device.androidVersion)
        devJson.put("sdk", device.sdk)
        devJson.put("build_id", device.buildId)
        devJson.put("build_fingerprint", device.buildFingerprint)
        devJson.put("abi", device.abi)
        json.put("device", devJson)

        val swJson = JSONObject()
        swJson.put("package", software.packageName)
        swJson.put("version_name", software.versionName ?: JSONObject.NULL)
        swJson.put("version_code", software.versionCode ?: JSONObject.NULL)
        json.put("software", swJson)

        val wlJson = JSONObject()
        wlJson.put("id", workload.id)
        wlJson.put("iteration", workload.iteration)
        json.put("workload", wlJson)

        val metricJson = JSONObject()
        metricJson.put("name", metric.name)
        metricJson.put("value", metric.value ?: JSONObject.NULL)
        metricJson.put("unit", metric.unit ?: JSONObject.NULL)
        json.put("metric", metricJson)

        json.put("source", source)
        json.put("capability", capability.name)
        json.put("reason", reason ?: JSONObject.NULL)

        return json
    }

    fun toJsonLine(): String = toJson().toString()
}
