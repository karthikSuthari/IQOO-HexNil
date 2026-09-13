package com.example.iqoo_hexnil.service

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log

class BootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == Intent.ACTION_BOOT_COMPLETED || 
            intent.action == Intent.ACTION_MY_PACKAGE_REPLACED) {
            
            val prefs = context.getSharedPreferences(HexnilBackgroundService.PREFS_NAME, Context.MODE_PRIVATE)
            val isEnabled = prefs.getBoolean(HexnilBackgroundService.KEY_BG_ENABLED, true) // default true for continuous monitoring

            Log.i("HEXNIL_BOOT", "[BOOT] Received ${intent.action}. Persistent BG monitoring configured: $isEnabled")
            if (isEnabled) {
                HexnilBackgroundService.start(context)
            }
        }
    }
}
