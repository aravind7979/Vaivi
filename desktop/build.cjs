const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

process.env.TAURI_SIGNING_PRIVATE_KEY = "dW50cnVzdGVkIGNvbW1lbnQ6IHJzaWduIGVuY3J5cHRlZCBzZWNyZXQga2V5ClJXUlRZMEl5RC8rM2lkSDVkTVBUeGlPczdHV2FKcHg0WkdsQWJhTVJybm42dFI5MWtEZ0FBQkFBQUFBQUFBQUFBQUlBQUFBQXNYTHRObjZwOEhLMFFKcmFNallzbm03Rlo3WEtKOFdiWFZ2aGR3Y3Y1aXZmY2UwOEk2d001ZVlLbUNUUkU2eGpSc09tUGpxWDZqbTFwWEJSMklSaGd3dkF2VjE2YklLRksrdzVBWjZlcyt5RExVd0xkNFFDZStlTnkzK2NYWUV5QWpqMXMxMUhkREE9Cg==";
process.env.TAURI_SIGNING_PRIVATE_KEY_PASSWORD = "";

try {
  console.log("Starting Tauri build...");
  execSync('npx @tauri-apps/cli build', { stdio: 'inherit' });
  console.log("Build completed successfully.");

  // Auto-generate latest.json
  const tauriConf = JSON.parse(fs.readFileSync(path.join(__dirname, 'src-tauri', 'tauri.conf.json'), 'utf8'));
  const version = tauriConf.version;
  
  const sigPath = path.join(__dirname, 'src-tauri', 'target', 'release', 'bundle', 'nsis', `Vaivi_${version}_x64-setup.exe.sig`);
  if (fs.existsSync(sigPath)) {
    const signature = fs.readFileSync(sigPath, 'utf8').trim();
    
    const latestJson = {
      version: version,
      notes: "Bug fixes and performance improvements.",
      pub_date: new Date().toISOString(),
      platforms: {
        "windows-x86_64": {
          signature: signature,
          url: `https://github.com/aravind7979/Vaivi/releases/download/v${version}/Vaivi_${version}_x64-setup.exe`
        }
      }
    };
    
    fs.writeFileSync(path.join(__dirname, 'latest.json'), JSON.stringify(latestJson, null, 2));
    console.log(`\n✅ Successfully generated latest.json for version ${version}!`);
    console.log(`You can now upload Vaivi_${version}_x64-setup.exe and latest.json to GitHub Releases.`);
  } else {
    console.error(`\n❌ Could not find signature file at ${sigPath}`);
  }

} catch (error) {
  console.error("Build failed.");
  process.exit(1);
}
