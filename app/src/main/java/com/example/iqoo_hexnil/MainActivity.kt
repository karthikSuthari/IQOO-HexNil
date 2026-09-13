package com.example.iqoo_hexnil

import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
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
import androidx.compose.material3.Scaffold
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
import com.example.iqoo_hexnil.ui.theme.HexnilMainAccent
import com.example.iqoo_hexnil.ui.theme.HexnilPrimaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryCard
import com.example.iqoo_hexnil.ui.theme.HexnilSecondaryText
import com.example.iqoo_hexnil.ui.theme.HexnilSuccess
import com.example.iqoo_hexnil.ui.theme.IQOOHEXNILTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            IQOOHEXNILTheme {
                Scaffold(
                    modifier = Modifier.fillMaxSize(),
                    containerColor = HexnilBackground
                ) { innerPadding ->
                    HexnilCompanionScreen(
                        modifier = Modifier.padding(innerPadding)
                    )
                }
            }
        }
    }
}

@Composable
fun HexnilCompanionScreen(modifier: Modifier = Modifier) {
    val scrollState = rememberScrollState()

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(HexnilBackground)
            .padding(horizontal = 20.dp, vertical = 16.dp)
            .verticalScroll(scrollState),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // App Header
        Column {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    text = "HEXNIL",
                    fontSize = 24.sp,
                    fontWeight = FontWeight.Black,
                    color = HexnilMainAccent,
                    letterSpacing = 2.sp
                )
                Spacer(modifier = Modifier.width(8.dp))
                Surface(
                    shape = RoundedCornerShape(4.dp),
                    color = HexnilSecondaryCard,
                    border = androidx.compose.foundation.BorderStroke(1.dp, HexnilBorder)
                ) {
                    Text(
                        text = "PHASE 1",
                        color = HexnilAccentGlow,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                    )
                }
            }
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = "Mobile Release-Validation Intelligence",
                color = HexnilSecondaryText,
                fontSize = 13.sp
            )
        }

        // Connection Status Card
        StatusCard()

        // Device Properties Card
        DevicePropertiesCard()

        // Architecture Boundary Note Card
        ArchitectureCard()

        Spacer(modifier = Modifier.height(16.dp))
    }
}

@Composable
fun StatusCard() {
    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .border(1.dp, HexnilBorder, RoundedCornerShape(12.dp)),
        color = HexnilCard
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(10.dp)
                    .background(HexnilSuccess, shape = CircleShape)
            )
            Spacer(modifier = Modifier.width(10.dp))
            Column {
                Text(
                    text = "Device Foundation Connected",
                    color = HexnilPrimaryText,
                    fontSize = 15.sp,
                    fontWeight = FontWeight.SemiBold
                )
                Text(
                    text = "ADB controller communication verified",
                    color = HexnilSecondaryText,
                    fontSize = 12.sp
                )
            }
        }
    }
}

@Composable
fun DevicePropertiesCard() {
    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .border(1.dp, HexnilBorder, RoundedCornerShape(12.dp)),
        color = HexnilCard
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                text = "TARGET HARDWARE IDENTITY",
                color = HexnilMainAccent,
                fontSize = 11.sp,
                fontWeight = FontWeight.Bold,
                letterSpacing = 1.sp
            )
            Spacer(modifier = Modifier.height(12.dp))

            PropertyRow("Manufacturer", Build.MANUFACTURER)
            PropertyRow("Model", Build.MODEL)
            PropertyRow("Device Codename", Build.DEVICE)
            PropertyRow("Android Release", Build.VERSION.RELEASE)
            PropertyRow("API / SDK Level", Build.VERSION.SDK_INT.toString())
            PropertyRow("Build ID", Build.ID)
            PropertyRow("ABI Architecture", Build.SUPPORTED_ABIS.firstOrNull() ?: "Unknown")

            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = "FINGERPRINT",
                color = HexnilSecondaryText,
                fontSize = 10.sp,
                fontWeight = FontWeight.Bold
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = Build.FINGERPRINT,
                color = HexnilPrimaryText,
                fontSize = 10.sp,
                fontFamily = FontFamily.Monospace,
                lineHeight = 14.sp,
                modifier = Modifier
                    .fillMaxWidth()
                    .background(HexnilSecondaryCard, RoundedCornerShape(6.dp))
                    .padding(8.dp)
            )
        }
    }
}

@Composable
fun PropertyRow(label: String, value: String) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 5.dp),
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Text(
            text = label,
            color = HexnilSecondaryText,
            fontSize = 13.sp
        )
        Text(
            text = value,
            color = HexnilPrimaryText,
            fontSize = 13.sp,
            fontWeight = FontWeight.Medium
        )
    }
}

@Composable
fun ArchitectureCard() {
    Surface(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .border(1.dp, HexnilBorder, RoundedCornerShape(12.dp)),
        color = HexnilSecondaryCard
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                text = "HOST-DEVICE ARCHITECTURE",
                color = HexnilSecondaryText,
                fontSize = 11.sp,
                fontWeight = FontWeight.Bold,
                letterSpacing = 1.sp
            )
            Spacer(modifier = Modifier.height(6.dp))
            Text(
                text = "ADB strictly belongs to the host controller machine. The on-device companion serves as the target runtime for later validation phases.",
                color = HexnilPrimaryText,
                fontSize = 12.sp,
                lineHeight = 18.sp
            )
        }
    }
}