package com.example.iqoo_hexnil.ui

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.iqoo_hexnil.data.HexnilRepository
import com.example.iqoo_hexnil.ui.theme.HexnilAccentGlow
import com.example.iqoo_hexnil.ui.theme.HexnilAccentSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilBackground
import com.example.iqoo_hexnil.ui.theme.HexnilBorder
import com.example.iqoo_hexnil.ui.theme.HexnilBorderSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilCard
import com.example.iqoo_hexnil.ui.theme.HexnilCyan
import com.example.iqoo_hexnil.ui.theme.HexnilFixed
import com.example.iqoo_hexnil.ui.theme.HexnilFixedSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilMainAccent
import com.example.iqoo_hexnil.ui.theme.HexnilPrimaryText
import com.example.iqoo_hexnil.ui.theme.HexnilRadius
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryCard
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSpacing

@Composable
fun AwaitingUpdateScreen(
    modifier: Modifier = Modifier
) {
    val scrollState = rememberScrollState()
    val preState = remember { HexnilRepository.getPreUpdateOsIdentity() }

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(HexnilBackground)
            .padding(horizontal = HexnilSpacing.screenHorizontal, vertical = HexnilSpacing.screenVertical)
            .verticalScroll(scrollState),
        verticalArrangement = Arrangement.spacedBy(HexnilSpacing.sectionSpacing)
    ) {
        // Hero Awaiting Card
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(HexnilRadius.hero))
                .border(BorderStroke(1.5.dp, HexnilMainAccent), RoundedCornerShape(HexnilRadius.hero)),
            color = HexnilCard
        ) {
            Column(
                modifier = Modifier.padding(20.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Box(
                    modifier = Modifier
                        .size(52.dp)
                        .clip(CircleShape)
                        .background(HexnilAccentSubtle)
                        .border(BorderStroke(1.dp, HexnilMainAccent), CircleShape),
                    contentAlignment = Alignment.Center
                ) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(32.dp),
                        color = HexnilMainAccent,
                        strokeWidth = 3.dp
                    )
                }

                Spacer(modifier = Modifier.height(16.dp))

                Text(
                    text = "V0 LOCKED",
                    color = HexnilFixed,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp
                )

                Spacer(modifier = Modifier.height(4.dp))

                Text(
                    text = "WAITING FOR REAL SYSTEM UPDATE",
                    color = HexnilPrimaryText,
                    fontSize = 17.sp,
                    fontWeight = FontWeight.Black,
                    letterSpacing = 0.5.sp
                )

                Spacer(modifier = Modifier.height(8.dp))

                Text(
                    text = "Hexnil is actively polling the ADB bridge and kernel properties for a genuine OS build, firmware, or security patch bump.",
                    color = HexnilSecondaryText,
                    fontSize = 12.sp,
                    lineHeight = 17.sp
                )
            }
        }

        // Locked Device OS Context
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(HexnilRadius.card))
                .border(BorderStroke(1.dp, HexnilBorder), RoundedCornerShape(HexnilRadius.card)),
            color = HexnilCard
        ) {
            Column(modifier = Modifier.padding(14.dp)) {
                Text(
                    text = "LOCKED PRE-UPDATE DEVICE PROFILE",
                    color = HexnilSecondaryText,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp
                )

                Spacer(modifier = Modifier.height(10.dp))

                InfoItem("Model", preState.model)
                InfoItem("Android Version", "Android ${preState.androidVersion} (SDK ${preState.sdkInt})")
                InfoItem("Build ID", preState.buildId)
                InfoItem("Security Patch", preState.securityPatchLevel)
                InfoItem("Boot Count", "${preState.bootCount}")
            }
        }

        // Core Scientific Rule Callout
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(HexnilRadius.card))
                .border(BorderStroke(1.dp, HexnilBorderSubtle), RoundedCornerShape(HexnilRadius.card)),
            color = HexnilSecondaryCard
        ) {
            Column(modifier = Modifier.padding(14.dp)) {
                Text(
                    text = "SCIENTIFIC INTEGRITY RULE",
                    color = HexnilMainAccent,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp
                )

                Spacer(modifier = Modifier.height(6.dp))

                Text(
                    text = "• No fake update button is provided.\n• No manual app benchmark creates V1.\n• No real update ➔ No V1 ➔ No validation.\n\nPlease apply the system software or security update via Android Settings ➔ System Update, then allow the device to restart.",
                    color = HexnilPrimaryText,
                    fontSize = 12.sp,
                    lineHeight = 18.sp
                )
            }
        }
    }
}

@Composable
private fun InfoItem(label: String, value: String) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(text = label, color = HexnilSecondaryText, fontSize = 12.sp)
        Text(text = value, color = HexnilCyan, fontSize = 11.sp, fontFamily = FontFamily.Monospace, fontWeight = FontWeight.Bold)
    }
}
