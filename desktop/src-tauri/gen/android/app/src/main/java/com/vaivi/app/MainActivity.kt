package com.vaivi.app

import android.content.Intent
import android.media.projection.MediaProjectionManager
import android.os.Bundle
import android.webkit.JavascriptInterface
import android.webkit.WebView
import androidx.activity.enableEdgeToEdge

class MainActivity : TauriActivity() {

  companion object {
      var activeWebView: WebView? = null
      fun sendFrameToJS(base64Uri: String) {
          activeWebView?.post {
              activeWebView?.evaluateJavascript("if(window.onReceiveScreenFrame) { window.onReceiveScreenFrame('$base64Uri'); }", null)
          }
      }
  }

  override fun onCreate(savedInstanceState: Bundle?) {
    enableEdgeToEdge()
    super.onCreate(savedInstanceState)
  }

  override fun onWebViewCreate(webView: WebView) {
    super.onWebViewCreate(webView)
    activeWebView = webView
    webView.addJavascriptInterface(VaiviNativeInterface(this@MainActivity), "VaiviNative")
  }

  private val SCREEN_CAPTURE_REQUEST_CODE = 999

  fun triggerScreenCaptureIntent() {
      val projectionManager = getSystemService(MEDIA_PROJECTION_SERVICE) as MediaProjectionManager
      startActivityForResult(projectionManager.createScreenCaptureIntent(), SCREEN_CAPTURE_REQUEST_CODE)
  }

  fun stopScreenCapture() {
      val intent = Intent(this, ScreenCaptureService::class.java).apply {
          action = "STOP"
      }
      startService(intent)
  }

  override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
      super.onActivityResult(requestCode, resultCode, data)
      if (requestCode == SCREEN_CAPTURE_REQUEST_CODE && resultCode == RESULT_OK && data != null) {
          val serviceIntent = Intent(this, ScreenCaptureService::class.java).apply {
              putExtra("code", resultCode)
              putExtra("data", data)
          }
          if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O) {
              startForegroundService(serviceIntent)
          } else {
              startService(serviceIntent)
          }
      }
  }
}

class VaiviNativeInterface(private val activity: MainActivity) {
    @JavascriptInterface
    fun startScreenCapture() {
        activity.runOnUiThread {
            activity.triggerScreenCaptureIntent()
        }
    }
    
    @JavascriptInterface
    fun stopScreenCapture() {
        activity.runOnUiThread {
            activity.stopScreenCapture()
        }
    }
}
