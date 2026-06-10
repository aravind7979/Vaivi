package com.vaivi.app

import android.app.Activity
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.PixelFormat
import android.hardware.display.DisplayManager
import android.hardware.display.VirtualDisplay
import android.media.ImageReader
import android.media.projection.MediaProjection
import android.media.projection.MediaProjectionManager
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.util.Base64
import androidx.core.app.NotificationCompat
import java.io.ByteArrayOutputStream

class ScreenCaptureService : Service() {

    companion object {
        var mediaProjection: MediaProjection? = null
        var isCapturing = false
    }

    private var virtualDisplay: VirtualDisplay? = null
    private var imageReader: ImageReader? = null
    private var lastFrameTime = 0L

    override fun onBind(intent: Intent?) = null

    private fun startNotification() {
        val channelId = "VaiviCapture"
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                channelId,
                "Vaivi AI Vision",
                NotificationManager.IMPORTANCE_LOW
            )
            (getSystemService(NOTIFICATION_SERVICE) as NotificationManager).createNotificationChannel(channel)
        }

        val notification = NotificationCompat.Builder(this, channelId)
            .setContentTitle("Vaivi AI")
            .setContentText("Screen analysis active")
            .setSmallIcon(android.R.drawable.ic_menu_camera)
            .build()
        
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            startForeground(1001, notification, android.content.pm.ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PROJECTION)
        } else {
            startForeground(1001, notification)
        }
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == "STOP") {
            stopCapture()
            stopSelf()
            return START_NOT_STICKY
        }

        val code = intent?.getIntExtra("code", Activity.RESULT_CANCELED) ?: Activity.RESULT_CANCELED
        val data = intent?.getParcelableExtra<Intent>("data")

        if (code == Activity.RESULT_OK && data != null && !isCapturing) {
            
            // REQUIRED: start the foreground notification INSIDE onStartCommand for MediaProjection, 
            // after validating Intent, to prevent premature OP_PROJECT_MEDIA denial on Android 14+!
            startNotification()

            val projectionManager = getSystemService(MEDIA_PROJECTION_SERVICE) as MediaProjectionManager
            mediaProjection = projectionManager.getMediaProjection(code, data)
            
            if (mediaProjection != null) {
                // REQUIRED ON ANDROID 14+ before creating VirtualDisplay!
                mediaProjection?.registerCallback(object : MediaProjection.Callback() {
                    override fun onStop() {
                        super.onStop()
                        stopSelf()
                    }
                }, Handler(Looper.getMainLooper()))
                
                isCapturing = true
                setupVirtualDisplay()
            }
        }
        return START_NOT_STICKY
    }

    private fun setupVirtualDisplay() {
        val width = 720
        val height = 1280
        val density = resources.displayMetrics.densityDpi

        imageReader = ImageReader.newInstance(width, height, PixelFormat.RGBA_8888, 2)
        
        virtualDisplay = mediaProjection?.createVirtualDisplay(
            "ScreenCapture",
            width, height, density,
            DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR,
            imageReader?.surface, null, null
        )

        imageReader?.setOnImageAvailableListener({ reader ->
            val image = reader.acquireLatestImage()
            if (image != null) {
                val now = System.currentTimeMillis()
                // Throttle to roughly 3 frames per second to save Webview RAM!
                if (now - lastFrameTime > 300) {
                    lastFrameTime = now
                    try {
                        val planes = image.planes
                        val buffer = planes[0].buffer
                        val pixelStride = planes[0].pixelStride
                        val rowStride = planes[0].rowStride
                        val rowPadding = rowStride - pixelStride * width

                        val bitmap = Bitmap.createBitmap(
                            width + rowPadding / pixelStride,
                            height,
                            Bitmap.Config.ARGB_8888
                        )
                        bitmap.copyPixelsFromBuffer(buffer)
                        
                        val cropped = Bitmap.createBitmap(bitmap, 0, 0, width, height)
                        val out = ByteArrayOutputStream()
                        cropped.compress(Bitmap.CompressFormat.JPEG, 40, out)
                        val base64 = Base64.encodeToString(out.toByteArray(), Base64.NO_WRAP)
                        
                        // Bridge it silently to the Webview UI Thread
                        MainActivity.sendFrameToJS("data:image/jpeg;base64,$base64")
                    } catch (e: Exception) {
                        e.printStackTrace()
                    }
                }
                image.close()
            }
        }, Handler(Looper.getMainLooper()))
    }

    private fun stopCapture() {
        isCapturing = false
        virtualDisplay?.release()
        imageReader?.close()
        mediaProjection?.stop()
        mediaProjection = null
    }

    override fun onDestroy() {
        stopCapture()
        super.onDestroy()
    }
}
