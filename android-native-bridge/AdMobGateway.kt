package com.vaivi.app

import android.app.Activity
import com.google.android.gms.ads.AdRequest
import com.google.android.gms.ads.MobileAds
import com.google.android.gms.ads.interstitial.InterstitialAd
import com.google.android.gms.ads.interstitial.InterstitialAdLoadCallback
import app.tauri.annotation.Command
import app.tauri.annotation.InvokeArg
import app.tauri.annotation.TauriPlugin
import app.tauri.plugin.Plugin
import app.tauri.plugin.Invoke

@TauriPlugin
class AdMobGateway(private val activity: Activity): Plugin(activity) {

    private var mInterstitialAd: InterstitialAd? = null
    // Use test ID during development. Swap to real ID before Play Store deployment.
    private val AD_UNIT_ID = "ca-app-pub-3940256099942544/1033173712"

    override fun load(webView: android.webkit.WebView?) {
        super.load(webView)
        // Initialize AdMob context securely via Tauri Load Hook
        MobileAds.initialize(activity) {}
        loadAd()
    }

    private fun loadAd() {
        val adRequest = AdRequest.Builder().build()
        InterstitialAd.load(activity, AD_UNIT_ID, adRequest, object : InterstitialAdLoadCallback() {
            override fun onAdLoaded(interstitialAd: InterstitialAd) {
                mInterstitialAd = interstitialAd
            }
            override fun onAdFailedToLoad(adError: com.google.android.gms.ads.LoadAdError) {
                mInterstitialAd = null
            }
        })
    }

    @Command
    fun showAd(invoke: Invoke) {
        activity.runOnUiThread {
            if (mInterstitialAd != null) {
                mInterstitialAd?.show(activity)
                // Preload the next ad instantly
                loadAd()
                invoke.resolve()
            } else {
                // Failsafe: if ad wasn't loaded, don't halt the user, just resolve.
                invoke.reject("Ad not ready or failed to load.")
                loadAd()
            }
        }
    }
}
