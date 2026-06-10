package com.vaivi.app

import android.app.Activity
import android.media.projection.MediaProjectionManager
import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.PixelFormat
import android.hardware.display.DisplayManager
import android.media.ImageReader
import android.util.Base64
import java.io.ByteArrayOutputStream
import app.tauri.annotation.Command
import app.tauri.annotation.InvokeArg
import app.tauri.annotation.TauriPlugin
import app.tauri.plugin.Plugin
import app.tauri.plugin.Invoke

@TauriPlugin
class MediaProjectionPlugin(private val activity: Activity): Plugin(activity) {

    private var currentInvoke: Invoke? = null
    private val REQUEST_CODE_SCREEN_CAPTURE = 1001

    @Command
    fun captureScreen(invoke: Invoke) {
        val manager = activity.getSystemService(Context.MEDIA_PROJECTION_SERVICE) as MediaProjectionManager
        currentInvoke = invoke
        activity.startActivityForResult(manager.createScreenCaptureIntent(), REQUEST_CODE_SCREEN_CAPTURE)
        // Note: You must intercept onActivityResult in MainActivity to catch the layout and return the Base64!
    }

    // This method should be called from your MainActivity's onActivityResult
    fun handleActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        if (requestCode != REQUEST_CODE_SCREEN_CAPTURE) return
        
        if (resultCode != Activity.RESULT_OK || data == null) {
            currentInvoke?.reject("Screen capture permission denied")
            return
        }

        // Logic to extract frame using ImageReader and MediaProjection
        // For simplicity in this bridge scaffolding, we mock the success return:
        // In full realization, you pipe VirtualDisplay -> ImageReader -> Bitmap -> Base64
        val dummyBase64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=" 
        
        val ret = app.tauri.plugin.JSObject()
        ret.put("base64", dummyBase64)
        currentInvoke?.resolve(ret)
    }
}
