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
import com.example.iqoo_hexnil.data.VerdictType
import com.example.iqoo_hexnil.ui.components.ResultBadge
import com.example.iqoo_hexnil.ui.components.SectionHeader
import com.example.iqoo_hexnil.ui.theme.HexnilAccentGlow
import com.example.iqoo_hexnil.ui.theme.HexnilBackground
import com.example.iqoo_hexnil.ui.theme.HexnilBorder
import com.example.iqoo_hexnil.ui.theme.HexnilCard
import com.example.iqoo_hexnil.ui.theme.HexnilInfo
import com.example.iqoo_hexnil.ui.theme.HexnilInfoSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilMainAccent
import com.example.iqoo_hexnil.ui.theme.HexnilPrimaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryCard
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSuccess
import com.example.iqoo_hexnil.ui.theme.HexnilWarning

@Composable
fun AiExplanationScreen(
    modifier: Modifier = Modifier
) {
    val scrollState = rememberScrollState()

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(HexnilBackground)
            .padding(horizontal = 16.dp, vertical = 12.dp)
            .verticalScroll(scrollState),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        // Section 1 Header: Measured Evidence (Authoritative)
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(12.dp))
                .border(1.dp, HexnilBorder, RoundedCornerShape(12.dp)),
            color = HexnilCard
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "MEASURED EVIDENCE (AUTHORITATIVE)",
                        color = HexnilMainAccent,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 1.sp
                    )
                    Surface(
                        shape = RoundedCornerShape(4.dp),
                        color = HexnilSecondaryCard,
                        border = BorderStroke(1.dp, HexnilSuccess)
                    ) {
                        Text(
                            text = "DETERMINISTIC",
                            color = HexnilSuccess,
                            fontSize = 9.sp,
                            fontWeight = FontWeight.Bold,
                            modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                        )
                    }
                }

                Spacer(modifier = Modifier.height(10.dp))

                EvidenceFactCard(
                    workload = "startup_01",
                    metric = "App Startup Latency",
                    finding = "Startup duration observed delta was +22.9% (+225.9 ms). 95% Confidence Interval [-324.9, +776.6] spans across zero with p=0.2196. Fails statistical significance requirement.",
                    verdict = VerdictType.INCONCLUSIVE
                )

                Spacer(modifier = Modifier.height(8.dp))

                EvidenceFactCard(
                    workload = "video_power_01",
                    metric = "Video Playback Duration",
                    finding = "Statistically significant shift detected (p=0.0116), but magnitude (+3.0%) is below the 5.0% meaningful engineering significance threshold.",
                    verdict = VerdictType.UNCHANGED
                )
            }
        }

        // Section 2: AI Interpretation Shell (Phase 8 Shell)
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(12.dp))
                .border(1.dp, HexnilInfo.copy(alpha = 0.5f), RoundedCornerShape(12.dp)),
            color = HexnilCard
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "AI INTERPRETATION (PHASE 8 SHELL)",
                        color = HexnilInfo,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 1.sp
                    )
                    Surface(
                        shape = RoundedCornerShape(4.dp),
                        color = HexnilInfoSubtle,
                        border = BorderStroke(1.dp, HexnilInfo)
                    ) {
                        Text(
                            text = "PREVIEW SHELL",
                            color = HexnilInfo,
                            fontSize = 9.sp,
                            fontWeight = FontWeight.Bold,
                            modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                        )
                    }
                }

                Spacer(modifier = Modifier.height(8.dp))

                Text(
                    text = "Deterministic statistical verdicts are authoritative. AI explains root causes and engineering trade-offs without hallucinating or overriding measured numbers.",
                    color = HexnilSecondaryText,
                    fontSize = 11.sp,
                    lineHeight = 15.sp
                )

                Spacer(modifier = Modifier.height(12.dp))

                AiNarrativeBlock(
                    title = "Root Cause Analysis",
                    body = "The apparent +22.9% cold startup slowdown is driven by run #3 variance (1561 ms vs 1201 ms) rather than a systematic regression. Background memory compaction and JIT compilation jitter during cold launch account for the wide confidence interval."
                )

                Spacer(modifier = Modifier.height(8.dp))

                AiNarrativeBlock(
                    title = "Release Recommendation",
                    body = "Increase startup iteration count from n=3 to n=10 before blocking release sign-off. Power and CPU throughput are verified stable (within 3.0% threshold)."
                )
            }
        }

        Spacer(modifier = Modifier.height(16.dp))
    }
}

@Composable
private fun EvidenceFactCard(
    workload: String,
    metric: String,
    finding: String,
    verdict: VerdictType
) {
    Surface(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(8.dp),
        color = HexnilSecondaryCard,
        border = BorderStroke(1.dp, HexnilBorder)
    ) {
        Column(modifier = Modifier.padding(10.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "$workload · $metric",
                    color = HexnilPrimaryText,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold
                )
                ResultBadge(verdict = verdict, isCompact = true)
            }
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = finding,
                color = HexnilSecondaryText,
                fontSize = 11.sp,
                lineHeight = 15.sp
            )
        }
    }
}

@Composable
private fun AiNarrativeBlock(
    title: String,
    body: String
) {
    Surface(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(8.dp),
        color = HexnilSecondaryCard,
        border = BorderStroke(1.dp, HexnilBorder)
    ) {
        Column(modifier = Modifier.padding(10.dp)) {
            Text(
                text = title,
                color = HexnilAccentGlow,
                fontSize = 12.sp,
                fontWeight = FontWeight.Bold
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = body,
                color = HexnilPrimaryText,
                fontSize = 11.sp,
                lineHeight = 15.sp
            )
        }
    }
}
