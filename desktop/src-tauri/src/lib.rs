use tauri::Manager;
use tauri::Emitter;
use tauri::RunEvent;
use tauri_plugin_autostart::ManagerExt;
use tauri_plugin_updater::UpdaterExt;
use tauri_plugin_global_shortcut::{GlobalShortcutExt, Shortcut, ShortcutState};
use screenshots::Screen;
use std::io::Cursor;

#[tauri::command]
fn take_screenshot() -> Result<Vec<u8>, String> {
    let screens = Screen::all().map_err(|e| e.to_string())?;
    let screen = screens.get(0).ok_or("No screen found")?;

    let image = screen.capture().map_err(|e| e.to_string())?;

    let mut buffer = Cursor::new(Vec::new());
    image::DynamicImage::ImageRgba8(image)
        .write_to(&mut buffer, image::ImageOutputFormat::Png)
        .map_err(|e| e.to_string())?;

    Ok(buffer.into_inner())
}

#[tauri::command]
fn hide_window(app_handle: tauri::AppHandle) {
    if let Some(window) = app_handle.get_webview_window("main") {
        let _ = window.hide();
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_updater::Builder::new().build())
        .plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| {
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.show();
                let _ = window.set_focus();
            }
        }))

        // 🔹 Global Shortcut (Alt + V)
        .plugin(
            tauri_plugin_global_shortcut::Builder::new()
                .with_handler(|app, shortcut, event| {
                    if event.state() == ShortcutState::Pressed {
                        if shortcut.matches(
                            tauri_plugin_global_shortcut::Modifiers::ALT,
                            tauri_plugin_global_shortcut::Code::KeyV,
                        ) {
                            if let Some(window) = app.get_webview_window("main") {
                                let is_visible = window.is_visible().unwrap_or(false);

                                if is_visible {
                                    let _ = window.hide();
                                } else {
                                    let _ = window.show();
                                    let _ = window.set_focus();
                                }
                            }
                        }
                    }
                })
                .build(),
        )

        // 🔹 Register shortcut & Stop initial flicker
        .setup(|app| {
            let shortcut = Shortcut::new(
                Some(tauri_plugin_global_shortcut::Modifiers::ALT),
                tauri_plugin_global_shortcut::Code::KeyV,
            );

            let _ = app.global_shortcut().register(shortcut);
            
            // Start hidden
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.hide(); 
            }
            
            // Start updater in background
            let app_handle = app.handle().clone();
            tauri::async_runtime::spawn(async move {
                if let Ok(updater) = app_handle.updater() {
                    if let Ok(Some(update)) = updater.check().await {
                        let _ = app_handle.emit("update-status", "Downloading update...");
                        let _ = update.download_and_install(|_, _| {}, || {}).await;
                        let _ = app_handle.emit("update-status", "Update installed. Restarting...");
                        // Small delay to let user see it if window is open
                        tokio::time::sleep(tokio::time::Duration::from_secs(3)).await;
                        app_handle.restart();
                    }
                }
            });

            // Enable autostart
            let _ = app.autolaunch().enable();

            Ok(())
        })

        // 🔹 Autostart
        .plugin(
            tauri_plugin_autostart::init(
                tauri_plugin_autostart::MacosLauncher::LaunchAgent,
                Some(vec!["--autostart"]),
            )
        )

        .invoke_handler(tauri::generate_handler![take_screenshot, hide_window])

        // 🔹 Prevent "X" button from actually destroying the window
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                api.prevent_close();
                let _ = window.hide();
            }
        })

        .build(tauri::generate_context!())
        .expect("error while building tauri application")

        // 🔹 Prevent OS exit loops → hide instead
        .run(|app_handle, event| {
            if let RunEvent::ExitRequested { api, .. } = event {
                api.prevent_exit();

                if let Some(window) = app_handle.get_webview_window("main") {
                    let _ = window.hide();
                }
            }
        });
}