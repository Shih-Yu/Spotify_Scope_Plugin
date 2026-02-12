# Scope Spotify Plugin (minimal)

This plugin makes the **current Spotify song title** (or a short template like “{song} by {artist}”) the **image prompt** in Scope. Your image pipeline (e.g. Stream Diffusion) then generates from that prompt.

**Important:** Scope only runs the preprocessor when it has **video or camera input**. So you must **enable camera or video** in Scope (not text-only) and leave the **Prompts** box empty. Then the prompt becomes whatever is playing in Spotify.

### Video input only (no text-only mode)

This plugin works **only when Scope is using video or camera input**. It does **not** work in text-only mode.

- **Why:** Scope runs the first processor (the preprocessor) only when there are video frames in the pipeline. In text-only mode the client never sends frames, so the Spotify preprocessor is never called and the song title is never used as the prompt.
- **What to do:** In Scope, turn on **Camera** or **Video** (file) so that frames are sent. Then the preprocessor runs and the current Spotify track becomes the prompt.
- **Text-only in the future:** Supporting text-only (song as prompt with no video) would require a change in Scope itself (e.g. to run the preprocessor even when no frames are sent). That would be an issue or PR in the [Scope repo](https://github.com/daydreamlive/scope).

---

## What you need to do (in order)

1. **Create a Spotify app** (one-time) and copy your Client ID and Client Secret.
2. **Install the plugin in Scope** (paste the plugin URL in Scope’s plugin settings).
3. **Set credentials** via environment variables where Scope runs (e.g. RunPod pod env: `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`).
4. **Log in to Spotify once** on the machine where Scope runs (run the auth script, open the URL in a browser, paste the redirect back).
5. **In Scope:** Pipeline = Stream Diffusion, Preprocessor = Spotify Prompt Generator. **Turn on camera or video input.** Clear the Prompts box. Play a song in Spotify, then press **Play**.

---

## Step 1: Create a Spotify app (one-time)

1. Open [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard) and log in with your Spotify account.
2. Click **Create app**. Give it a name (e.g. “Scope”) and accept the terms.
3. Open your new app. Copy **Client ID** and **Client Secret** (click “Show” next to Client Secret) and save them somewhere safe.
4. Click **Settings**. Under **Redirect URI**, add exactly:  
   `http://127.0.0.1:8888/callback`  
   Save.

---

## Step 2: Install the plugin in Scope

1. In **Scope**, go to the place where you add or manage plugins (often **Settings** or **Plugins**).
2. When it asks for a plugin URL or “Install from Git”, paste this (use the full line, no spaces at the start or end):

   ```
   https://github.com/Shih-Yu/Spotify_Scope_Plugin.git
   ```

3. Confirm or install. Wait until Scope says the plugin is installed.

**Yes — you do need to install the plugin.** The auth script only does the one-time Spotify login; the plugin itself must be installed in Scope using the URL above.

---

## Step 3: Add your credentials where Scope runs

The preprocessor reads credentials from **environment variables** only (no credential fields in the Scope UI). Set them when you create or edit your RunPod pod under **Pod → Edit → Environment Variables** (or **Secrets**). That way both Spotify and Scope’s pipeline (e.g. Stream Diffusion) have what they need:

- **Spotify (this plugin):**
  - `SPOTIFY_CLIENT_ID` = your Spotify Client ID
  - `SPOTIFY_CLIENT_SECRET` = your Spotify Client Secret
  - `SPOTIFY_REDIRECT_URI` = redirect URL (optional; default `http://127.0.0.1:8888/callback` — must match the Redirect URI in your [Spotify app settings](https://developer.spotify.com/dashboard))
  - `SPOTIFY_HEADLESS` = set to `false` only if running Scope locally and you want the auth script to open a browser (default `true` for RunPod)
- **Hugging Face (Scope / Stream Diffusion):**
  - `HF_TOKEN` = your [Hugging Face access token](https://huggingface.co/settings/tokens) (required for downloading models)

Restart the pod after changing env vars if Scope is already running.

---

## Step 4: One-time Spotify login (auth script)

The plugin needs a **one-time login** to your Spotify account on the machine where Scope runs (e.g. your RunPod). After that, it reuses the saved token.

**On RunPod:**

1. Open the **web terminal** (or SSH) for your pod.
2. The auth script lives in the **plugin repo**. If the repo isn’t on the pod yet, run:
   ```bash
   cd /app
   git clone https://github.com/Shih-Yu/Spotify_Scope_Plugin.git
   cd Spotify_Scope_Plugin
   ```
   If the pod doesn't have pip (`python3 -m pip` says "No module named pip"), install it first:
   ```bash
   apt-get update && apt-get install -y python3-pip
   ```
   (If that fails, try `python3 -m ensurepip --upgrade`.) Then install the plugin's dependencies (so `spotipy` is available):
   ```bash
   python3 -m pip install .
   ```
3. Make sure the pod has your credentials (Step 3). Then run:
   ```bash
   python3 scripts/spotify_auth.py
   ```
4. The script will print a **URL**. On **your own computer**, open that URL in a browser, log in to Spotify if asked, and click **Allow**.
5. The browser will redirect to a page that may not load; that’s OK. **Copy the entire URL** from the browser’s address bar (it will look like `http://127.0.0.1:8888/callback?code=...`).
6. Back in the **RunPod terminal**, when the script asks for it, **paste that URL** and press Enter. When it says “Authentication successful”, you’re done. You don’t need to run this again unless you revoke the app or change accounts.

---

## Step 5: Use it in Scope

1. Set **Pipeline** to **Stream Diffusion** (or your image pipeline).
2. Set **Preprocessor** to **Spotify Prompt Generator**.
3. **Enable video or camera input** — Scope only runs the preprocessor when it has frames. If you use text-only (no camera/video), the Spotify preprocessor is never called and the prompt will not be the song title.
4. **Leave the Prompts box empty** so the preprocessor’s prompt (the song) is used.
5. In Spotify (same account as in Step 4), **start playing a song**.
6. In Scope, press **Play**. The prompt sent to the pipeline will be the current song title (default template `{song}`) or whatever you set in **Prompt Template** (e.g. `{song} by {artist}`).

The **Prompts** box in Scope’s UI may keep showing old text (e.g. “blooming flowers”); Scope often doesn’t update that field from the preprocessor. The song title is still sent to the pipeline internally. Check the **generated image** (it should follow the current track) and the **server logs** (`Spotify preprocessor: prompt from track: [song] by [artist]`) to confirm the plugin is working.

---

## If something doesn’t work

- **Plugin not installed:** Make sure you added the plugin URL in Scope (Step 2) and that Scope finished installing it.
- **“Nothing happens” when I press Play:** Restart Scope (or the pod) after Step 4 so it can load the token. Check that you ran the auth script **on the same pod** where Scope runs and that credentials (Step 3) are set there too.
- **RunPod: “python: command not found”:** Use `python3` instead of `python` (e.g. `python3 scripts/spotify_auth.py`).

### Preprocessor in chain but never runs

Scope **only calls the first processor when there are video frames** in its queue. In **text-only** mode (no camera, no video), the client never sends frames, so the Spotify preprocessor is never run and the prompt stays whatever is in the Prompts box.

- **Fix:** In Scope, **enable camera or video input** (e.g. turn on the camera or upload a short video). Then press Play with the Prompts box **empty**. You should see `Spotify preprocessor: __call__ invoked` and `prompt from track: [song] by [artist]` in the server logs, and the generated image will follow the song title.
- **Credentials:** Set `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` in the environment where Scope runs (e.g. RunPod pod env).
- **Token:** Run the auth script once on the same machine as Scope (`python3 scripts/spotify_auth.py`), then restart Scope so it picks up the token.

For more on how Scope runs the chain, see **`scope-plugin-skill/`** in this repo and the [Pipeline architecture](https://docs.daydream.live/scope/reference/architecture/pipelines) docs.

---

## Developer / plugin build reference

This repo includes **`scope-plugin-skill/`**, which describes how to build Scope plugins and how preprocessors fit into the pipeline chain. Use it when changing this plugin or debugging “preprocessor in chain but never runs”:

- **`scope-plugin-skill/skills/create-scope-plugin/SKILL.md`** — Process and rules for building a Scope plugin.
- **`scope-plugin-skill/skills/create-scope-plugin/reference.md`** — Technical reference: imports, schema, pipeline types (including preprocessor), I/O format, troubleshooting.

Official docs: [Plugin development](https://docs.daydream.live/scope/guides/plugin-development), [Pipeline architecture](https://docs.daydream.live/scope/reference/architecture/pipelines).

---

## Optional: change the prompt text

In Scope’s Input/Settings when the Spotify preprocessor is selected you can set:

- **Template theme** — Dropdown of preset styles: **Dreamy / abstract**, **Lyrics + style** (song/artist), **Music video still**, **Minimal** (lyrics only), **Song + artist**, or **Custom** (use your own template below).
- **Prompt Template** — Used when Template theme is **Custom**. Use `{song}`, `{artist}`, and when lyrics are on, `{lyrics}` (e.g. `{song} by {artist}` or `{lyrics}, style of {artist}`).
- **Fallback Prompt** — Used when no track is playing (default: “Abstract flowing colors and shapes”).

You can also set `SPOTIFY_TEMPLATE_THEME`, `SPOTIFY_PROMPT_TEMPLATE`, and `SPOTIFY_FALLBACK_PROMPT` in the environment if you prefer.

### Lyrics synced with the song

You can drive the prompt from the **current lyric line** so the image changes with the song:

1. Turn **Use lyrics** on in the preprocessor settings.
2. Keep **Synced with song** on (default). The plugin fetches time-synced lyrics from **LRCLIB** (free, no API key) and uses the line at the current playback position from Spotify.
3. Set **Prompt Template** to something like `{lyrics}` or `{song}: {lyrics}` so the prompt updates as the track plays.

If synced lyrics aren’t found for a track, or you turn **Synced with song** off, the plugin falls back to plain lyrics from Lyrics.ovh (a short snippet up to **Lyrics max length** characters). No Genius or other API keys are required for synced or plain lyrics.

---

## Companion lyrics app (sing along)

A small **companion app** shows synced lyrics in your browser while Scope runs the visuals. It uses the **same Spotify token** as the plugin (no second login) and the same LRCLIB synced lyrics.

**Run it on the same machine as Scope** (e.g. your PC or RunPod). Open the lyrics page in a browser (or a second screen) and sing along while Scope generates the images.

### Setup and run

1. **Install the optional dependencies** (FastAPI + Uvicorn):
   ```bash
   uv sync --extra lyrics-app
   ```
   or with pip:
   ```bash
   pip install -e ".[lyrics-app]"
   ```

2. **Set the same Spotify env vars** as Scope (or rely on your shell/env):
   - `SPOTIFY_CLIENT_ID`
   - `SPOTIFY_CLIENT_SECRET`

3. **Start the lyrics server** from the repo root:
   ```bash
   uv run python -m lyrics_app.server
   ```
   By default it listens on **http://0.0.0.0:8765**. Set `LYRICS_APP_PORT` to use another port.

4. **Open in a browser**: go to **http://localhost:8765** (or your machine's hostname/port). Play a song in Spotify; the page shows the current lyric line and updates in sync.

The app polls `/api/now` every second for the current track and lyric line. If no track is playing, it shows "Play something on Spotify".

---

## License

MIT.
