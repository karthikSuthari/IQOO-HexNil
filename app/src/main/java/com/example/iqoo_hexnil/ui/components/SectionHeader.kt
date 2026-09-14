package com.example.iqoo_hexnil.ui.components

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.iqoo_hexnil.ui.theme.HexnilAccentGlow
import com.example.iqoo_hexnil.ui.theme.HexnilMainAccent
import com.example.iqoo_hexnil.ui.theme.HexnilPrimaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryText

@Composable
fun SectionHeader(
    category: String,
    title: String? = null,
    subtitle: String? = null,
    actionText: String? = null,
    onActionClick: (() -> Unit)? = null,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier
            .fillMaxWidth()
            .padding(top = 10.dp, bottom = 4.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = category.uppercase(),
                color = HexnilMainAccent,
                fontSize = 11.sp,
                fontWeight = FontWeight.Bold,
                letterSpacing = 1.1.sp,
                maxLines = 1,
                modifier = Modifier.weight(1f, fill = false)
            )
            if (actionText != null) {
                Text(
                    text = actionText,
                    color = HexnilAccentGlow,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.SemiBold,
                    letterSpacing = 0.5.sp,
                    maxLines = 1,
                    modifier = if (onActionClick != null) Modifier.clickable { onActionClick() } else Modifier
                )
            }
        }

        if (title != null) {
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = title,
                color = HexnilPrimaryText,
                fontSize = 18.sp,
                fontWeight = FontWeight.Bold
            )
        }

        if (subtitle != null) {
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = subtitle,
                color = HexnilSecondaryText,
                fontSize = 13.sp,
                lineHeight = 19.sp
            )
        }
    }
}

@Composable
fun SectionHeader(
    title: String,
    actionLabel: String? = null,
    onActionClick: (() -> Unit)? = null,
    modifier: Modifier = Modifier
) {
    SectionHeader(
        category = title,
        actionText = actionLabel,
        onActionClick = onActionClick,
        modifier = modifier
    )
}


