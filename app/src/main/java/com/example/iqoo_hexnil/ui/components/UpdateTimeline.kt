package com.example.iqoo_hexnil.ui.components

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.horizontalScroll
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
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.iqoo_hexnil.data.HexnilLifecycleState
import com.example.iqoo_hexnil.ui.theme.HexnilAccentGlow
import com.example.iqoo_hexnil.ui.theme.HexnilAccentSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilBackground
import com.example.iqoo_hexnil.ui.theme.HexnilBorder
import com.example.iqoo_hexnil.ui.theme.HexnilBorderSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilCard
import com.example.iqoo_hexnil.ui.theme.HexnilMainAccent
import com.example.iqoo_hexnil.ui.theme.HexnilPrimaryText
import com.example.iqoo_hexnil.ui.theme.HexnilRadius
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryCard
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSuccess

@Composable
fun UpdateTimeline(
    currentState: HexnilLifecycleState,
    modifier: Modifier = Modifier
) {
    val scrollState = rememberScrollState()

    Surface(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(HexnilRadius.card))
            .border(BorderStroke(1.dp, HexnilBorderSubtle), RoundedCornerShape(HexnilRadius.card)),
        color = HexnilCard
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            // Header: Current Lifecycle Active Callout
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(text = "🔄", fontSize = 14.sp)
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        text = "OS UPDATE LIFECYCLE",
                        color = HexnilPrimaryText,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 1.sp
                    )
                }

                Surface(
                    shape = RoundedCornerShape(HexnilRadius.badge),
                    color = HexnilAccentSubtle,
                    border = BorderStroke(1.dp, HexnilMainAccent.copy(alpha = 0.5f))
                ) {
                    Text(
                        text = "STEP ${currentState.step}/14",
                        color = HexnilAccentGlow,
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                    )
                }
            }

            Spacer(modifier = Modifier.height(6.dp))

            // Current state status narrative
            Text(
                text = "${currentState.label}: ${currentState.description}",
                color = HexnilSecondaryText,
                fontSize = 12.sp,
                lineHeight = 16.sp
            )

            Spacer(modifier = Modifier.height(14.dp))

            // Horizontal Scrollable Stepper Pipeline
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .horizontalScroll(scrollState),
                verticalAlignment = Alignment.CenterVertically
            ) {
                HexnilLifecycleState.values().forEachIndexed { index, state ->
                    val isCompleted = state.step < currentState.step
                    val isActive = state == currentState
                    val isUpcoming = state.step > currentState.step

                    val circleColor = when {
                        isActive -> HexnilMainAccent
                        isCompleted -> HexnilSuccess
                        else -> HexnilSecondaryCard
                    }
                    val textColor = when {
                        isActive -> HexnilPrimaryText
                        isCompleted -> HexnilSecondaryText
                        else -> HexnilSecondaryText.copy(alpha = 0.4f)
                    }

                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        modifier = Modifier.padding(horizontal = 4.dp)
                    ) {
                        Box(
                            modifier = Modifier
                                .size(24.dp)
                                .clip(CircleShape)
                                .background(circleColor)
                                .border(
                                    BorderStroke(
                                        1.dp,
                                        if (isActive) HexnilAccentGlow else HexnilBorderSubtle
                                    ),
                                    CircleShape
                                ),
                            contentAlignment = Alignment.Center
                        ) {
                            Text(
                                text = if (isCompleted) "✓" else "${state.step}",
                                color = if (isActive || isCompleted) Color.White else HexnilSecondaryText,
                                fontSize = 10.sp,
                                fontWeight = FontWeight.Bold
                            )
                        }

                        Spacer(modifier = Modifier.height(4.dp))

                        Text(
                            text = state.label.take(10),
                            color = textColor,
                            fontSize = 9.sp,
                            fontWeight = if (isActive) FontWeight.Bold else FontWeight.Normal,
                            maxLines = 1
                        )
                    }

                    if (index < HexnilLifecycleState.values().size - 1) {
                        Box(
                            modifier = Modifier
                                .width(16.dp)
                                .height(2.dp)
                                .background(
                                    if (isCompleted) HexnilSuccess.copy(alpha = 0.5f) else HexnilBorderSubtle
                                )
                        )
                    }
                }
            }
        }
    }
}
