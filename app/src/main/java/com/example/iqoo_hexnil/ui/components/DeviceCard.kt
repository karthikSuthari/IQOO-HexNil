package com.example.iqoo_hexnil.ui.components

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.iqoo_hexnil.data.DeviceHardwareInfo
import com.example.iqoo_hexnil.data.HardwareEvidenceState
import com.example.iqoo_hexnil.ui.theme.HexnilAccentGlow
import com.example.iqoo_hexnil.ui.theme.HexnilBackground
import com.example.iqoo_hexnil.ui.theme.HexnilBorder
import com.example.iqoo_hexnil.ui.theme.HexnilCard
import com.example.iqoo_hexnil.ui.theme.HexnilError
import com.example.iqoo_hexnil.ui.theme.HexnilMainAccent
import com.example.iqoo_hexnil.ui.theme.HexnilPrimaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryCard
import com.example.iqoo_hexnil.ui.theme.HexnilRadius
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryCard
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSpacing
import com.example.iqoo_hexnil.ui.theme.HexnilSuccess
import com.example.iqoo_hexnil.ui.theme.HexnilWarning

@Composable
fun DeviceCard(
    device: DeviceHardwareInfo,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(HexnilRadius.hero))
            .border(1.dp, HexnilBorder, RoundedCornerShape(HexnilRadius.hero)),
        color = HexnilCard
    ) {
        Column(modifier = Modifier.padding(HexnilSpacing.cardPadding)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "TARGET HARDWARE STATE",
                    color = HexnilMainAccent,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp
                )
                Row(verticalAlignment = Alignment.CenterVertically) {
                    val (dotColor, statusLabel) = when (device.evidenceState) {
                        HardwareEvidenceState.LIVE -> Pair(HexnilSuccess, "LIVE EVIDENCE")
                        HardwareEvidenceState.UNAVAILABLE -> Pair(HexnilWarning, "NO LIVE EVIDENCE")
                        HardwareEvidenceState.UNSUPPORTED -> Pair(HexnilError, "UNSUPPORTED")
                        HardwareEvidenceState.STALE_CACHED -> Pair(HexnilSecondaryText, "CACHED SNAPSHOT")
                    }
                    Box(
                        modifier = Modifier
                            .size(8.dp)
                            .background(dotColor, CircleShape)
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        text = statusLabel,
                        color = dotColor,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold
                    )
                }
            }

            Spacer(modifier = Modifier.height(14.dp))

            // Quick Hardware Stats Tiles
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                DeviceStatusTile(
                    label = "Model",
                    value = "${device.manufacturer} ${device.model}",
                    sub = "Codename: ${device.codename}",
                    modifier = Modifier.weight(1f)
                )
                DeviceStatusTile(
                    label = "OS Platform",
                    value = "Android ${device.androidRelease}",
                    sub = "SDK Level: ${device.sdkInt}",
                    modifier = Modifier.weight(1f)
                )
            }

            Spacer(modifier = Modifier.height(10.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                DeviceStatusTile(
                    label = "Battery Proxy",
                    value = if (device.batteryPercent != null) "${device.batteryPercent}%" else "Unavailable",
                    sub = if (device.chargingState == "NO_LIVE_EVIDENCE") "No live evidence" else device.chargingState,
                    modifier = Modifier.weight(1f)
                )
                DeviceStatusTile(
                    label = "Thermals",
                    value = if (device.thermalStatus == "NO_LIVE_EVIDENCE") "Unavailable" else device.thermalStatus,
                    sub = if (device.thermalStatus == "UNSUPPORTED") "API Not Supported" else "Hardware State",
                    modifier = Modifier.weight(1f)
                )
            }
        }
    }
}

@Composable
fun BuildIdentityCard(
    device: DeviceHardwareInfo,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(HexnilRadius.card))
            .border(1.dp, HexnilBorder, RoundedCornerShape(HexnilRadius.card)),
        color = HexnilCard
    ) {
        Column(modifier = Modifier.padding(HexnilSpacing.cardPadding)) {
            Text(
                text = "BUILD FINGERPRINT & PROVENANCE",
                color = HexnilMainAccent,
                fontSize = 12.sp,
                fontWeight = FontWeight.Bold,
                letterSpacing = 1.sp
            )
            Spacer(modifier = Modifier.height(12.dp))

            BuildPropertyRow("Build ID", device.buildId)
            BuildPropertyRow("ABI Architecture", device.abi)

            Spacer(modifier = Modifier.height(10.dp))
            Text(
                text = "SYSTEM FINGERPRINT",
                color = HexnilSecondaryText,
                fontSize = 11.sp,
                fontWeight = FontWeight.Bold
            )
            Spacer(modifier = Modifier.height(4.dp))
            Surface(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(HexnilRadius.md),
                color = HexnilSecondaryCard
            ) {
                Text(
                    text = device.fingerprint,
                    color = HexnilPrimaryText,
                    fontSize = 11.sp,
                    fontFamily = FontFamily.Monospace,
                    lineHeight = 16.sp,
                    modifier = Modifier.padding(10.dp)
                )
            }
        }
    }
}

@Composable
private fun DeviceStatusTile(
    label: String,
    value: String,
    sub: String,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier
            .clip(RoundedCornerShape(HexnilRadius.md))
            .border(1.dp, HexnilBorder, RoundedCornerShape(HexnilRadius.md)),
        color = HexnilSecondaryCard
    ) {
        Column(modifier = Modifier.padding(12.dp)) {
            Text(text = label, color = HexnilSecondaryText, fontSize = 12.sp)
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = value,
                color = HexnilPrimaryText,
                fontSize = 15.sp,
                fontWeight = FontWeight.Bold,
                maxLines = 1
            )
            Spacer(modifier = Modifier.height(2.dp))
            Text(
                text = sub,
                color = HexnilAccentGlow,
                fontSize = 11.sp,
                maxLines = 1
            )
        }
    }
}

@Composable
private fun BuildPropertyRow(label: String, value: String) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 5.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(text = label, color = HexnilSecondaryText, fontSize = 13.sp)
        Text(
            text = value,
            color = HexnilPrimaryText,
            fontSize = 13.sp,
            fontWeight = FontWeight.Medium,
            fontFamily = FontFamily.Monospace
        )
    }
}

