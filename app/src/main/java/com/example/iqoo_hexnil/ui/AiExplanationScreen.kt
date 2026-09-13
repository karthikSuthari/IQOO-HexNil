package com.example.iqoo_hexnil.ui

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
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
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.iqoo_hexnil.data.AiExplanation
import com.example.iqoo_hexnil.data.ClaimAssessment
import com.example.iqoo_hexnil.data.ComparisonAnalysis
import com.example.iqoo_hexnil.data.EvidenceReference
import com.example.iqoo_hexnil.data.ExplanationSource
import com.example.iqoo_hexnil.data.HexnilRepository
import com.example.iqoo_hexnil.data.VerdictType
import com.example.iqoo_hexnil.ui.components.ResultBadge
import com.example.iqoo_hexnil.ui.components.SectionHeader
import com.example.iqoo_hexnil.ui.theme.HexnilAccentGlow
import com.example.iqoo_hexnil.ui.theme.HexnilBackground
import com.example.iqoo_hexnil.ui.theme.HexnilBorder
import com.example.iqoo_hexnil.ui.theme.HexnilCard
import com.example.iqoo_hexnil.ui.theme.HexnilError
import com.example.iqoo_hexnil.ui.theme.HexnilErrorSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilInfo
import com.example.iqoo_hexnil.ui.theme.HexnilInfoSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilMainAccent
import com.example.iqoo_hexnil.ui.theme.HexnilPrimaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryCard
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSuccess
import com.example.iqoo_hexnil.ui.theme.HexnilSuccessSubtle
import com.example.iqoo_hexnil.ui.theme.HexnilWarning
import com.example.iqoo_hexnil.ui.theme.HexnilWarningSubtle

@Composable
fun AiExplanationScreen(
    analysis: ComparisonAnalysis,
    initialExplanation: AiExplanation? = null,
    modifier: Modifier = Modifier
) {
    val scrollState = rememberScrollState()
    var selectedSource by remember {
        mutableStateOf(initialExplanation?.source ?: ExplanationSource.DETERMINISTIC_ANALYSIS)
    }

    val explanation = remember(selectedSource, analysis.comparisonId) {
        initialExplanation?.takeIf { it.source == selectedSource }
            ?: HexnilRepository.getAiExplanation(analysis.comparisonId, selectedSource)
    }

    // Empty / Invalid state check
    if (analysis.metricResults.isEmpty()) {
        Box(
            modifier = modifier
                .fillMaxSize()
                .background(HexnilBackground)
                .padding(24.dp),
            contentAlignment = Alignment.Center
        ) {
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text(
                    text = "NO EVIDENCE AVAILABLE",
                    color = HexnilWarning,
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.sp
                )
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = "Comparison contains zero metric observations. Run differential workload iterations to collect evidence.",
                    color = HexnilSecondaryText,
                    fontSize = 12.sp,
                    lineHeight = 16.sp
                )
            }
        }
        return
    }

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(HexnilBackground)
            .padding(horizontal = 16.dp, vertical = 12.dp)
            .verticalScroll(scrollState),
        verticalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        // Section 1: Authoritative Deterministic Verdict Banner
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
                            text = "DETERMINISTIC VERDICT",
                            color = HexnilSecondaryText,
                            fontSize = 10.sp,
                            fontWeight = FontWeight.Bold,
                            letterSpacing = 1.sp
                        )
                        Spacer(modifier = Modifier.height(2.dp))
                        Text(
                            text = "Mathematical Ground Truth",
                            color = HexnilPrimaryText,
                            fontSize = 15.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }
                    ResultBadge(verdict = VerdictType.UNCHANGED)
                }

                Spacer(modifier = Modifier.height(10.dp))

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Column {
                        Text(text = "Comparison ID", color = HexnilSecondaryText, fontSize = 10.sp)
                        Text(text = analysis.comparisonId, color = HexnilPrimaryText, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                    }
                    Column {
                        Text(text = "Baseline -> Update", color = HexnilSecondaryText, fontSize = 10.sp)
                        Text(text = "${analysis.v0ExperimentId} -> ${analysis.v1ExperimentId}", color = HexnilPrimaryText, fontSize = 11.sp, fontFamily = FontFamily.Monospace)
                    }
                    Column {
                        Text(text = "Hardware", color = HexnilSecondaryText, fontSize = 10.sp)
                        Text(text = analysis.deviceModel, color = HexnilPrimaryText, fontSize = 11.sp)
                    }
                }
            }
        }

        // Section 2: Explanation Source Toggle Bar (Groq vs Deterministic vs Fallback)
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(10.dp))
                .border(1.dp, HexnilBorder, RoundedCornerShape(10.dp)),
            color = HexnilSecondaryCard
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(4.dp),
                horizontalArrangement = Arrangement.SpaceEvenly
            ) {
                SourceTabChip(
                    label = "Deterministic",
                    isSelected = selectedSource == ExplanationSource.DETERMINISTIC_ANALYSIS,
                    activeColor = HexnilInfo,
                    onClick = { selectedSource = ExplanationSource.DETERMINISTIC_ANALYSIS }
                )
                SourceTabChip(
                    label = "AI (Groq)",
                    isSelected = selectedSource == ExplanationSource.GROQ_AI,
                    activeColor = HexnilMainAccent,
                    onClick = { selectedSource = ExplanationSource.GROQ_AI }
                )
                SourceTabChip(
                    label = "Fallback",
                    isSelected = selectedSource == ExplanationSource.DETERMINISTIC_FALLBACK,
                    activeColor = HexnilWarning,
                    onClick = { selectedSource = ExplanationSource.DETERMINISTIC_FALLBACK }
                )
            }
        }

        // Section 3: AI Explanation Card
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(12.dp))
                .border(
                    1.dp,
                    when (explanation.source) {
                        ExplanationSource.GROQ_AI -> HexnilMainAccent.copy(alpha = 0.6f)
                        ExplanationSource.DETERMINISTIC_FALLBACK -> HexnilWarning.copy(alpha = 0.6f)
                        else -> HexnilInfo.copy(alpha = 0.5f)
                    },
                    RoundedCornerShape(12.dp)
                ),
            color = HexnilCard
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Box(
                            modifier = Modifier
                                .size(8.dp)
                                .clip(CircleShape)
                                .background(
                                    when (explanation.source) {
                                        ExplanationSource.GROQ_AI -> HexnilMainAccent
                                        ExplanationSource.DETERMINISTIC_FALLBACK -> HexnilWarning
                                        else -> HexnilInfo
                                    }
                                )
                        )
                        Spacer(modifier = Modifier.width(6.dp))
                        Text(
                            text = explanation.source.label,
                            color = when (explanation.source) {
                                ExplanationSource.GROQ_AI -> HexnilMainAccent
                                ExplanationSource.DETERMINISTIC_FALLBACK -> HexnilWarning
                                else -> HexnilInfo
                            },
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            letterSpacing = 0.5.sp
                        )
                    }

                    Surface(
                        shape = RoundedCornerShape(4.dp),
                        color = HexnilSecondaryCard,
                        border = BorderStroke(1.dp, HexnilBorder)
                    ) {
                        Text(
                            text = if (explanation.isCached) "CACHED VERIFIED" else "LIVE INFERENCE",
                            color = HexnilSecondaryText,
                            fontSize = 9.sp,
                            fontWeight = FontWeight.Bold,
                            modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                        )
                    }
                }

                if (explanation.model != null) {
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = "Model: ${explanation.model}",
                        color = HexnilSecondaryText,
                        fontSize = 10.sp,
                        fontFamily = FontFamily.Monospace
                    )
                }

                Spacer(modifier = Modifier.height(10.dp))

                Text(
                    text = explanation.summary,
                    color = HexnilPrimaryText,
                    fontSize = 13.sp,
                    lineHeight = 18.sp
                )
            }
        }

        // Section 4: What Was Measured (Observed Changes)
        SectionHeader(
            category = "WHAT WAS MEASURED (FACTS)",
            actionText = "${explanation.observedChanges.size} OBSERVED"
        )
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            explanation.observedChanges.take(6).forEach { fact ->
                Surface(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(8.dp))
                        .border(1.dp, HexnilBorder, RoundedCornerShape(8.dp)),
                    color = HexnilCard
                ) {
                    Row(
                        modifier = Modifier.padding(12.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Box(
                            modifier = Modifier
                                .size(6.dp)
                                .clip(CircleShape)
                                .background(HexnilInfo)
                        )
                        Spacer(modifier = Modifier.width(10.dp))
                        Text(
                            text = fact,
                            color = HexnilPrimaryText,
                            fontSize = 11.sp,
                            lineHeight = 15.sp,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                }
            }
        }

        // Section 5: Why Verdict Was Reached (Statistical Interpretation)
        SectionHeader(
            category = "WHY THE VERDICT WAS REACHED",
            actionText = "STATISTICAL EVIDENCE"
        )
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(10.dp))
                .border(1.dp, HexnilBorder, RoundedCornerShape(10.dp)),
            color = HexnilCard
        ) {
            Column(modifier = Modifier.padding(14.dp)) {
                Text(
                    text = explanation.statisticalInterpretation,
                    color = HexnilSecondaryText,
                    fontSize = 11.sp,
                    lineHeight = 16.sp
                )
            }
        }

        // Section 6: Claim Impact & Assessments
        SectionHeader(
            category = "UPDATE CLAIM ASSESSMENTS",
            actionText = "${explanation.claimAssessments.size} CLAIMS"
        )
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            explanation.claimAssessments.forEach { claim ->
                Surface(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(10.dp))
                        .border(1.dp, HexnilBorder, RoundedCornerShape(10.dp)),
                    color = HexnilCard
                ) {
                    Column(modifier = Modifier.padding(12.dp)) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                text = claim.claimId,
                                color = HexnilMainAccent,
                                fontSize = 11.sp,
                                fontWeight = FontWeight.Bold,
                                fontFamily = FontFamily.Monospace
                            )
                            ClaimStatusChip(status = claim.status)
                        }
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            text = claim.claimText,
                            color = HexnilPrimaryText,
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Medium
                        )
                        Spacer(modifier = Modifier.height(6.dp))
                        Text(
                            text = claim.explanation,
                            color = HexnilSecondaryText,
                            fontSize = 11.sp,
                            lineHeight = 15.sp
                        )
                    }
                }
            }
        }

        // Section 7: Evidence Limitations & Safeguards
        SectionHeader(
            category = "EVIDENCE LIMITATIONS",
            actionText = "TRANSPARENCY"
        )
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(10.dp))
                .border(1.dp, HexnilBorder, RoundedCornerShape(10.dp)),
            color = HexnilCard
        ) {
            Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                explanation.limitations.forEach { lim ->
                    Row(verticalAlignment = Alignment.Top) {
                        Text(text = "•", color = HexnilWarning, fontSize = 12.sp, modifier = Modifier.padding(end = 6.dp))
                        Text(text = lim, color = HexnilSecondaryText, fontSize = 11.sp, lineHeight = 15.sp)
                    }
                }
            }
        }

        // Section 8: Recommended Next Step
        SectionHeader(
            category = "RECOMMENDED NEXT INVESTIGATION",
            actionText = "ACTION ITEM"
        )
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(10.dp))
                .border(1.dp, HexnilMainAccent.copy(alpha = 0.4f), RoundedCornerShape(10.dp)),
            color = HexnilCard
        ) {
            Row(modifier = Modifier.padding(14.dp), verticalAlignment = Alignment.Top) {
                Box(
                    modifier = Modifier
                        .size(8.dp)
                        .clip(CircleShape)
                        .background(HexnilMainAccent)
                        .padding(top = 4.dp)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = explanation.recommendedNextStep,
                    color = HexnilPrimaryText,
                    fontSize = 12.sp,
                    lineHeight = 16.sp,
                    fontWeight = FontWeight.Medium
                )
            }
        }

        // Section 9: Traceable Evidence References
        SectionHeader(
            category = "EVIDENCE REFERENCES (LINEAGE)",
            actionText = "${explanation.evidenceReferences.size} REFS"
        )
        Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
            explanation.evidenceReferences.forEach { ref ->
                Surface(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(8.dp))
                        .border(1.dp, HexnilBorder, RoundedCornerShape(8.dp)),
                    color = HexnilSecondaryCard
                ) {
                    Row(
                        modifier = Modifier.padding(10.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Text(
                                    text = "[${ref.referenceId}] ${ref.type.uppercase()}: ",
                                    color = HexnilInfo,
                                    fontSize = 10.sp,
                                    fontWeight = FontWeight.Bold,
                                    fontFamily = FontFamily.Monospace
                                )
                                Text(
                                    text = ref.identifier,
                                    color = HexnilPrimaryText,
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.Bold,
                                    fontFamily = FontFamily.Monospace
                                )
                            }
                            if (ref.artifactPath != null) {
                                Text(
                                    text = ref.artifactPath,
                                    color = HexnilSecondaryText,
                                    fontSize = 9.sp,
                                    fontFamily = FontFamily.Monospace
                                )
                            }
                        }
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(16.dp))
    }
}

@Composable
private fun SourceTabChip(
    label: String,
    isSelected: Boolean,
    activeColor: Color,
    onClick: () -> Unit
) {
    Surface(
        modifier = Modifier
            .clip(RoundedCornerShape(6.dp))
            .clickable(onClick = onClick),
        color = if (isSelected) activeColor.copy(alpha = 0.2f) else Color.Transparent,
        border = if (isSelected) BorderStroke(1.dp, activeColor) else null
    ) {
        Text(
            text = label,
            color = if (isSelected) activeColor else HexnilSecondaryText,
            fontSize = 10.sp,
            fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal,
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp)
        )
    }
}

@Composable
private fun ClaimStatusChip(status: String) {
    val (color, bg) = when (status) {
        "SUPPORTED" -> Pair(HexnilSuccess, HexnilSuccessSubtle)
        "CONTRADICTED" -> Pair(HexnilError, HexnilErrorSubtle)
        "INCONCLUSIVE" -> Pair(HexnilWarning, HexnilWarningSubtle)
        else -> Pair(HexnilSecondaryText, HexnilSecondaryCard)
    }

    Surface(
        shape = RoundedCornerShape(4.dp),
        color = bg,
        border = BorderStroke(1.dp, color.copy(alpha = 0.5f))
    ) {
        Text(
            text = status,
            color = color,
            fontSize = 9.sp,
            fontWeight = FontWeight.Bold,
            modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
        )
    }
}
