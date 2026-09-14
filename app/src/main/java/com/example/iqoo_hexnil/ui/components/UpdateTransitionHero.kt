package com.example.iqoo_hexnil.ui.components

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
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
import com.example.iqoo_hexnil.data.DeviceOsIdentity
import com.example.iqoo_hexnil.data.TransitionType
import com.example.iqoo_hexnil.data.UpdateTransition
import com.example.iqoo_hexnil.ui.theme.HexnilAccentGlow
import com.example.iqoo_hexnil.ui.theme.HexnilAccentSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilBorder
import com.example.iqoo_hexnil.ui.theme.HexnilBorderFocus
import com.example.iqoo_hexnil.ui.theme.HexnilBorderSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilCard
import com.example.iqoo_hexnil.ui.theme.HexnilCyan
import com.example.iqoo_hexnil.ui.theme.HexnilCyanSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilMainAccent
import com.example.iqoo_hexnil.ui.theme.HexnilPrimaryText
import com.example.iqoo_hexnil.ui.theme.HexnilRadius
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryCard
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSuccess

@Composable
fun UpdateTransitionHero(
    transition: UpdateTransition,
    onClick: (() -> Unit)? = null,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(HexnilRadius.hero))
            .border(BorderStroke(1.dp, HexnilBorder), RoundedCornerShape(HexnilRadius.hero))
            .then(if (onClick != null) Modifier.clickable { onClick() } else Modifier),
        color = HexnilCard
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            // Header: Category Tag & Transition Badge
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(
                        modifier = Modifier
                            .size(8.dp)
                            .background(HexnilMainAccent, CircleShape)
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        text = "REAL OS UPDATE EVENT",
                        color = HexnilMainAccent,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 1.sp
                    )
                }

                Surface(
                    shape = RoundedCornerShape(HexnilRadius.badge),
                    color = HexnilAccentSubtle,
                    border = BorderStroke(1.dp, HexnilBorderFocus.copy(alpha = 0.5f))
                ) {
                    Text(
                        text = transition.transitionType.label.uppercase(),
                        color = HexnilAccentGlow,
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 3.dp)
                    )
                }
            }

            Spacer(modifier = Modifier.height(14.dp))

            // Dual Node Visual: V0 (Before) -> Real Update -> V1 (After)
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                // V0 Node
                OsStateBox(
                    label = "V0 (PRE-UPDATE)",
                    state = transition.preState,
                    isPost = false,
                    modifier = Modifier.weight(1f)
                )

                // Central Transition Indicator
                Column(
                    modifier = Modifier.padding(horizontal = 8.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Text(text = "➔", color = HexnilMainAccent, fontSize = 20.sp, fontWeight = FontWeight.Bold)
                    Spacer(modifier = Modifier.height(2.dp))
                    Text(
                        text = "${transition.durationMinutes}m OTA",
                        color = HexnilSecondaryText,
                        fontSize = 9.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }

                // V1 Node
                OsStateBox(
                    label = "V1 (POST-UPDATE)",
                    state = transition.postState,
                    isPost = true,
                    modifier = Modifier.weight(1f)
                )
            }

            Spacer(modifier = Modifier.height(14.dp))

            // Reboot & Verification Context Line
            Surface(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(HexnilRadius.sm),
                color = HexnilSecondaryCard,
                border = BorderStroke(1.dp, HexnilBorderSubtle)
            ) {
                Row(
                    modifier = Modifier.padding(10.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(text = "🛡️", fontSize = 13.sp)
                    Spacer(modifier = Modifier.width(8.dp))
                    Column {
                        Text(
                            text = "Transition Context: ${transition.rebootContext}",
                            color = HexnilSecondaryText,
                            fontSize = 11.sp,
                            lineHeight = 15.sp
                        )
                        Spacer(modifier = Modifier.height(2.dp))
                        Text(
                            text = "Detected: ${transition.detectedAt} • Boot Count: ${transition.preState.bootCount} ➔ ${transition.postState.bootCount}",
                            color = HexnilCyan,
                            fontSize = 10.sp,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun OsStateBox(
    label: String,
    state: DeviceOsIdentity,
    isPost: Boolean,
    modifier: Modifier = Modifier
) {
    val borderColor = if (isPost) HexnilSuccess.copy(alpha = 0.6f) else HexnilBorder
    val labelColor = if (isPost) HexnilSuccess else HexnilSecondaryText

    Surface(
        modifier = modifier
            .clip(RoundedCornerShape(HexnilRadius.md))
            .border(BorderStroke(1.dp, borderColor), RoundedCornerShape(HexnilRadius.md)),
        color = HexnilSecondaryCard
    ) {
        Column(modifier = Modifier.padding(10.dp)) {
            Text(
                text = label,
                color = labelColor,
                fontSize = 10.sp,
                fontWeight = FontWeight.Bold,
                letterSpacing = 0.5.sp
            )

            Spacer(modifier = Modifier.height(4.dp))

            Text(
                text = "Android ${state.androidVersion}",
                color = HexnilPrimaryText,
                fontSize = 14.sp,
                fontWeight = FontWeight.Bold
            )

            Spacer(modifier = Modifier.height(2.dp))

            Text(
                text = state.buildId,
                color = HexnilSecondaryText,
                fontSize = 10.sp,
                fontFamily = FontFamily.Monospace,
                maxLines = 1
            )

            Spacer(modifier = Modifier.height(4.dp))

            Surface(
                shape = RoundedCornerShape(4.dp),
                color = HexnilCard,
                border = BorderStroke(1.dp, HexnilBorderSubtle)
            ) {
                Text(
                    text = "Patch: ${state.securityPatchLevel}",
                    color = if (isPost) HexnilCyan else HexnilSecondaryText,
                    fontSize = 9.sp,
                    fontFamily = FontFamily.Monospace,
                    modifier = Modifier.padding(horizontal = 4.dp, vertical = 2.dp)
                )
            }
        }
    }
}
