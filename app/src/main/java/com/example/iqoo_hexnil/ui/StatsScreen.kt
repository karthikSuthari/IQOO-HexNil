package com.example.iqoo_hexnil.ui

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
import com.example.iqoo_hexnil.ui.theme.HexnilAccentGlow
import com.example.iqoo_hexnil.ui.theme.HexnilBackground
import com.example.iqoo_hexnil.ui.theme.HexnilBorder
import com.example.iqoo_hexnil.ui.theme.HexnilCard
import com.example.iqoo_hexnil.ui.theme.HexnilError
import com.example.iqoo_hexnil.ui.theme.HexnilMainAccent
import com.example.iqoo_hexnil.ui.theme.HexnilPrimaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryCard
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSuccess
import com.example.iqoo_hexnil.ui.theme.HexnilWarning

data class MetricStatCardData(
    val workloadId: String,
    val metricName: String,
    val v0Mean: String,
    val v1Mean: String,
    val delta: String,
    val percentDelta: String,
    val ci95: String,
    val pValue: String,
    val effectSize: String,
    val verdict: String,
    val reason: String
)

@Composable
fun StatsScreen(
    comparisonId: String = "CMP-20260913-001",
    modifier: Modifier = Modifier
) {
    val scrollState = rememberScrollState()

    val stats = listOf(
        MetricStatCardData(
            workloadId = "cpu_01",
            metricName = "compute_duration_ms",
            v0Mean = "3224.5 ms",
            v1Mean = "3202.0 ms",
            delta = "-22.5 ms",
            percentDelta = "-0.70%",
            ci95 = "[-305.5, +260.5]",
            pValue = "p=0.7648",
            effectSize = "d=-0.20",
            verdict = "UNCHANGED",
            reason = "Change (-0.7%) is within the 5.0% meaningful engineering threshold."
        ),
        MetricStatCardData(
            workloadId = "video_power_01",
            metricName = "workload_duration_ms",
            v0Mean = "12356.3 ms",
            v1Mean = "12733.5 ms",
            delta = "+377.2 ms",
            percentDelta = "+3.05%",
            ci95 = "[+201.0, +553.5]",
            pValue = "p=0.0116",
            effectSize = "d=5.32",
            verdict = "UNCHANGED",
            reason = "Statistically significant (p<0.05), but delta (+3.0%) is below 5.0% threshold."
        ),
        MetricStatCardData(
            workloadId = "startup_01",
            metricName = "startup_duration_ms",
            v0Mean = "985.0 ms",
            v1Mean = "1210.9 ms",
            delta = "+225.9 ms",
            percentDelta = "+22.93%",
            ci95 = "[-324.9, +776.6]",
            pValue = "p=0.2196",
            effectSize = "d=1.02",
            verdict = "INCONCLUSIVE",
            reason = "Observed delta not statistically significant (95% CI spans across zero)."
        ),
        MetricStatCardData(
            workloadId = "scroll_01",
            metricName = "scroll_duration_ms",
            v0Mean = "4605.1 ms",
            v1Mean = "4533.1 ms",
            delta = "-72.0 ms",
            percentDelta = "-1.56%",
            ci95 = "[-461.7, +317.6]",
            pValue = "p=0.5099",
            effectSize = "d=-0.46",
            verdict = "UNCHANGED",
            reason = "Change (-1.6%) is within acceptable engineering threshold."
        ),
        MetricStatCardData(
            workloadId = "video_power_01",
            metricName = "playback_duration_ms",
            v0Mean = "9449.0 ms",
            v1Mean = "9443.6 ms",
            delta = "-5.4 ms",
            percentDelta = "-0.06%",
            ci95 = "[-226.4, +215.6]",
            pValue = "p=0.9260",
            effectSize = "d=-0.06",
            verdict = "UNCHANGED",
            reason = "No material difference detected between V0 and V1."
        )
    )

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(HexnilBackground)
            .padding(horizontal = 20.dp, vertical = 12.dp)
            .verticalScroll(scrollState),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        // Summary Card
        StatsAuditHeaderCard(comparisonId = comparisonId)

        // Metric Comparison Cards
        stats.forEach { card ->
            MetricStatisticalCard(data = card)
        }

        Spacer(modifier = Modifier.height(16.dp))
    }
}

@Composable
fun StatsAuditHeaderCard(comparisonId: String) {
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
                    text = "PHASE 6 STATISTICAL VERDICTS",
                    color = HexnilMainAccent,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp
                )
                Text(
                    text = comparisonId,
                    color = HexnilAccentGlow,
                    fontSize = 11.sp,
                    fontFamily = FontFamily.Monospace,
                    fontWeight = FontWeight.Bold
                )
            }

            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = "Evidence Coverage: 9/13 claims/metrics with sufficient measured evidence",
                color = HexnilPrimaryText,
                fontSize = 12.sp,
                fontWeight = FontWeight.SemiBold
            )
            Spacer(modifier = Modifier.height(8.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                VerdictCountBadge("UNCHANGED: 8", HexnilSuccess, Modifier.weight(1f))
                VerdictCountBadge("INCONCLUSIVE: 5", HexnilWarning, Modifier.weight(1f))
                VerdictCountBadge("REGRESSION: 0", HexnilError, Modifier.weight(1f))
            }
        }
    }
}

@Composable
fun VerdictCountBadge(label: String, color: androidx.compose.ui.graphics.Color, modifier: Modifier = Modifier) {
    Surface(
        modifier = modifier
            .clip(RoundedCornerShape(4.dp))
            .border(1.dp, HexnilBorder, RoundedCornerShape(4.dp)),
        color = HexnilSecondaryCard
    ) {
        Text(
            text = label,
            color = color,
            fontSize = 9.sp,
            fontWeight = FontWeight.Bold,
            modifier = Modifier.padding(vertical = 4.dp, horizontal = 4.dp),
            maxLines = 1
        )
    }
}

@Composable
fun MetricStatisticalCard(data: MetricStatCardData) {
    val verdictColor = when (data.verdict) {
        "IMPROVEMENT" -> HexnilSuccess
        "UNCHANGED" -> HexnilSuccess
        "INCONCLUSIVE" -> HexnilWarning
        "REGRESSION" -> HexnilError
        else -> HexnilSecondaryText
    }

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
                Column {
                    Text(
                        text = data.workloadId,
                        color = HexnilSecondaryText,
                        fontSize = 11.sp,
                        fontFamily = FontFamily.Monospace
                    )
                    Text(
                        text = data.metricName,
                        color = HexnilPrimaryText,
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Bold
                    )
                }
                Surface(
                    shape = RoundedCornerShape(4.dp),
                    color = HexnilSecondaryCard,
                    border = androidx.compose.foundation.BorderStroke(1.dp, verdictColor)
                ) {
                    Text(
                        text = "[${data.verdict}]",
                        color = verdictColor,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Black,
                        modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                    )
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            // Delta & Significance Row
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text(
                    text = "Delta: ${data.delta} (${data.percentDelta})",
                    color = HexnilMainAccent,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold,
                    fontFamily = FontFamily.Monospace
                )
                Text(
                    text = "${data.pValue} · ${data.effectSize}",
                    color = HexnilSecondaryText,
                    fontSize = 11.sp,
                    fontFamily = FontFamily.Monospace
                )
            }

            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = "95% CI: ${data.ci95}",
                color = HexnilSecondaryText,
                fontSize = 11.sp,
                fontFamily = FontFamily.Monospace
            )
            Spacer(modifier = Modifier.height(6.dp))
            Text(
                text = data.reason,
                color = HexnilSecondaryText,
                fontSize = 11.sp,
                lineHeight = 15.sp
            )
        }
    }
}
