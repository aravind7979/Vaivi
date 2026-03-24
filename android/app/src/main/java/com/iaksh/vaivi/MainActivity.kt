package com.iaksh.vaivi

import android.app.Activity
import android.content.Context
import android.content.Intent
import android.media.projection.MediaProjectionManager
import android.net.Uri
import android.os.Bundle
import android.provider.Settings
import android.widget.Button
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {

    private lateinit projectionManager: MediaProjectionManager

    private val screenCaptureIntentLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == Activity.RESULT_OK) {
            val serviceIntent = Intent(this, ScreenCaptureService::class.java).apply {
                putExtra("code", result.resultCode)
                putExtra("data", result.data)
            }
            startForegroundService(serviceIntent)
            
            // Now start the overlay to trigger captures
            startService(Intent(this, OverlayService::class.java))
            finish() // Close main UI since assistant is now running
        } else {
            Toast.makeText(this, "Screen capture permission denied", Toast.LENGTH_SHORT).show()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Very basic layout in code for scaffolding
        val btnStart = Button(this).apply {
            text = "Start Vaivi Assistant"
            setOnClickListener { checkPermissionsAndStart() }
        }
        setContentView(btnStart)
        
        projectionManager = getSystemService(Context.MEDIA_PROJECTION_SERVICE) as MediaProjectionManager
    }

    private fun checkPermissionsAndStart() {
        if (!Settings.canDrawOverlays(this)) {
            val intent = Intent(
                Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                Uri.parse("package:$packageName")
            )
            startActivity(intent)
            Toast.makeText(this, "Please grant overlay permission and return", Toast.LENGTH_LONG).show()
            return
        }

        // Request MediaProjection
        screenCaptureIntentLauncher.launch(projectionManager.createScreenCaptureIntent())
    }
}
