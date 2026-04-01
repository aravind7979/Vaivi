use tauri::{Manager, Emitter};
use tauri_plugin_global_shortcut::{GlobalShortcutExt, Shortcut, ShortcutState};
use screenshots::Screen;
use image::{ImageBuffer, Rgba};
use std::io::Cursor;

#[tauri::command]
fn take_screenshot() -> Result<Vec<u8>, String> {
    let screens = Screen::all().map_err(|e| e.to_string())?;
    let screen = screens.get(0).ok_or("No screen found")?;

    let image = screen.capture().map_err(|e| e.to_string())?;

    // Convert to PNG
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
        .plugin(tauri_plugin_opener::init())
        .plugin(
            tauri_plugin_global_shortcut::Builder::new()
                .with_handler(|app, shortcut, event| {
                    if event.state() == ShortcutState::Pressed {
                        if shortcut.matches(tauri_plugin_global_shortcut::Modifiers::ALT, tauri_plugin_global_shortcut::Code::KeyV) {
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
        .setup(|app| {
            let shortcut = Shortcut::new(
                Some(tauri_plugin_global_shortcut::Modifiers::ALT),
                tauri_plugin_global_shortcut::Code::KeyV,
            );
            let _ = app.global_shortcut().register(shortcut);
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![take_screenshot, hide_window])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
