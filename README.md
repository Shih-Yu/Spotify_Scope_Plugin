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
2. **Set up a RunPod pod** (use the [Scope template](https://console.runpod.io/deploy?template=aca8mw9ivw)) and **set credentials** via the pod’s environment variables (`SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, etc.).
3. **Log in to Spotify once** on the machine where Scope runs (run the auth script, open the URL in a browser, paste the redirect back).
4. **Install the plugin in Scope** (paste the plugin URL in Scope’s plugin settings).
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

## Step 2: Add your credentials where Scope runs

**Set up the pod with the Scope template:** Use RunPod’s Scope template to deploy a pod that already has Scope configured: **[Deploy with Scope template](https://console.runpod.io/deploy?template=aca8mw9ivw)**.

The preprocessor reads credentials from **environment variables** only (no credential fields in the Scope UI). When you create or edit your RunPod pod, add the variables below under **Pod → Edit → Environment Variables** (or **Secrets**). That way both Spotify and Scope’s pipeline (e.g. Stream Diffusion) have what they need:

- **Spotify (this plugin):**
  - `SPOTIFY_CLIENT_ID` = your Spotify Client ID
  - `SPOTIFY_CLIENT_SECRET` = your Spotify Client Secret
  - `SPOTIFY_REDIRECT_URI` = redirect URL (optional; default `http://127.0.0.1:8888/callback` — must match the Redirect URI in your [Spotify app settings](https://developer.spotify.com/dashboard))
  - `SPOTIFY_HEADLESS` = set to `false` only if running Scope locally and you want the auth script to open a browser (default `true` for RunPod)
- **Hugging Face (Scope / Stream Diffusion):**
  - `HF_TOKEN` = your [Hugging Face access token](https://huggingface.co/settings/tokens) (required for downloading models)

Restart the pod after changing env vars if Scope is already running.

---

## Step 3: One-time Spotify login (auth script)

The plugin needs a **one-time login** to your Spotify account on the machine where Scope runs (e.g. your RunPod). After that, it reuses the saved token.

**On RunPod:**

1. Open the **web terminal** (or SSH) for your pod.
2. Go to the **plugin repo**. If it isn’t on the pod yet, clone it:

   ```bash
   cd /app
   git clone https://github.com/Shih-Yu/Spotify_Scope_Plugin.git
   cd Spotify_Scope_Plugin
   ```

   If the repo is already there, run: `cd /app/Spotify_Scope_Plugin`

3. **Install dependencies (required).** You must do this before running the auth script. If pip is missing, install it first:

   ```bash
   apt-get update && apt-get install -y python3-pip
   ```

   ```bash
   python3 -m pip install .
   ```

4. Make sure the pod has your credentials (Step 2). Then run the auth script:

   ```bash
   python3 scripts/spotify_auth.py
   ```

5. The script will print a **URL**. On **your own computer**, open that URL in a browser, log in to Spotify if asked, and click **Allow**.
6. The browser will redirect to a page that may not load; that’s OK. **Copy the entire URL** from the browser’s address bar (it will look like `http://127.0.0.1:8888/callback?code=...`).
7. Back in the **RunPod terminal**, when the script asks for it, **paste that URL** and press Enter. When it says “Authentication successful”, you’re done. You don’t need to run this again unless you revoke the app or change accounts.

---

## Step 4: Install the plugin in Scope

1. In **Scope**, go to the place where you add or manage plugins (often **Settings** or **Plugins**).
2. When it asks for a plugin URL or “Install from Git”, paste this (use the full line, no spaces at the start or end):

   ```
   https://github.com/Shih-Yu/Spotify_Scope_Plugin.git
   ```

3. Confirm or install. Wait until Scope says the plugin is installed.

**Yes — you do need to install the plugin.** The auth script only does the one-time Spotify login; the plugin itself must be installed in Scope using the URL above.

---

## Step 5: Use it in Scope

1. Set **Pipeline** to **Stream Diffusion** (or your image pipeline).
2. Set **Preprocessor** to **Spotify Prompt Generator**.
3. **Enable video or camera input** — Scope only runs the preprocessor when it has frames. If you use text-only (no camera/video), the Spotify preprocessor is never called and the prompt will not be the song title.
4. **Leave the Prompts box empty** so the preprocessor’s prompt (the song) is used.
5. In Spotify (same account as in Step 3), **start playing a song**.
6. In Scope, press **Play**. The prompt is built from the current song and lyrics using the **Template theme** you chose (e.g. Dreamy / abstract, Song + artist).

The **Prompts** box in Scope’s UI may keep showing old text (e.g. “blooming flowers”); Scope often doesn’t update that field from the preprocessor. The song title is still sent to the pipeline internally. Check the **generated image** (it should follow the current track) and the **server logs** (see below) to confirm the plugin is working.

### How to confirm the template is used (logs)

The **container/Docker logs** (image pull, “create container”, “start container”) are not Scope’s application logs. To see that the Spotify preprocessor is using your selected template and the actual prompt:

1. **Find Scope’s process logs** — On RunPod, open the **Logs** for the pod (or the Scope service/container) and look for lines that come from the Scope app after it has started (e.g. when you press Play).
2. **Look for these lines** (they are logged at WARNING level so they are not filtered out):
   - `Spotify preprocessor: template_theme=...` — shows which theme is active (`dreamy_abstract`, `lyrics_style`, `song_artist`, etc.).
   - `Spotify preprocessor: prompt sent to pipeline: ...` — shows the first ~120 characters of the prompt sent to the image pipeline. That is the prompt built from your template + current song/lyrics.
   - **`Spotify preprocessor: pipeline FPS ≈ X.X`** — logged about every 5 seconds. This is the rate at which the preprocessor is invoked (one call per frame), so it matches the **output FPS** of the image pipeline.
   - **`Avg ms per frame: get_track=... lyrics=... passthrough=...`** — appears in the same 5-second summary. Use these numbers to see which part of the plugin is costing time: **get_track** (Spotify API, cached by default), **lyrics** (synced or plain lyrics fetch), **passthrough** (tensor copy to device). If one of these is high (e.g. get_track > 50 ms), that step is reducing your FPS.

If you never see `Spotify preprocessor: __call__ invoked`, the preprocessor is not being called (e.g. no video/camera input).

---

## If something doesn’t work

- **`ModuleNotFoundError: No module named 'spotipy'`:** You ran the auth script before installing dependencies. From the plugin repo root run `python3 -m pip install .`, then run `python3 scripts/spotify_auth.py` again. See Step 3, item 3 (install dependencies).
- **Plugin not installed:** Make sure you added the plugin URL in Scope (Step 4) and that Scope finished installing it.
- **“Unknown error” when installing the plugin from Scope’s UI:** Scope often doesn’t show the real error. To see the actual cause:
  1. On the **same machine (or RunPod) where Scope runs**, open a terminal and use the **same Python environment** Scope uses (e.g. the pod’s `python3` or the venv Scope was started with).
  2. Run:  
     `pip install "git+https://github.com/Shih-Yu/Spotify_Scope_Plugin.git"`  
     (or `python3 -m pip install "git+https://github.com/Shih-Yu/Spotify_Scope_Plugin.git"`).
  3. Check the output for the real error. Common causes: **network** (can’t reach GitHub), **dependency conflict** (e.g. `spotipy` or `torch`), or **Python version** (Scope expects Python 3.12+). Fix the reported error, then try installing again from Scope’s UI, or leave the plugin installed via pip and restart Scope.
- **“Nothing happens” when I press Play:** Restart Scope (or the pod) after Step 3 so it can load the token. Check that you ran the auth script **on the same pod** where Scope runs and that credentials (Step 2) are set there too.
- **RunPod: “python: command not found”:** Use `python3` instead of `python` (e.g. `python3 scripts/spotify_auth.py`).

### Low FPS (e.g. ~4 FPS on H100 / RunPod when you expect 15–20)

The Spotify plugin only supplies the **prompt**; it does not run the image model. FPS is determined by the **image pipeline** (e.g. Stream Diffusion): number of diffusion steps, resolution, and pipeline settings. So even on an H100 or other strong GPU, you may see ~4 FPS if the pipeline is configured for quality (many steps, high resolution). In RunPod logs, look for **`Spotify preprocessor: pipeline FPS ≈ X.X`** (logged every ~5 seconds) to see the actual frame rate. To get closer to 15–20 FPS, tune **Scope’s Stream Diffusion (or image pipeline) settings**: fewer inference steps, lower output resolution, and any “turbo” or speed-oriented mode the pipeline offers. The plugin cannot increase FPS; only the image pipeline can.

**Output resolution has a large impact on throughput.** If your output resolution is set high (e.g. 1280×720), try dropping it to something lower like **832×480** or **640×382** in Scope’s pipeline settings to improve FPS. This is especially relevant when using video or camera input.

**FPS drops when using the plugin (e.g. 14 FPS without plugin → 6 FPS with it)**  
The plugin runs once per frame. To find what’s slowing you down, check the **avg ms per frame** line in the logs (get_track, lyrics, passthrough). The plugin now **caches** the current Spotify track for 0.4 seconds (configurable: `SPOTIFY_TRACK_CACHE_SECONDS`) and caches lyrics per track, so the API isn’t hit every frame. Lyrics (time-synced) and rotating style word are **built-in**. For **maximum FPS**, use **Template theme “Song + artist”** so the prompt is shorter (song + artist only in the template); you can switch to a lyrics-heavy theme (e.g. Dreamy / abstract) when FPS is acceptable.

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

## How the config works

Credentials are **not** in the Scope UI. Set **SPOTIFY_CLIENT_ID**, **SPOTIFY_CLIENT_SECRET** (and optionally **SPOTIFY_REDIRECT_URI**) in the **environment** where Scope runs (e.g. RunPod pod env, or `.env`). See Step 2 in the main steps above.

In Scope’s **Input/Settings** when the Spotify preprocessor is selected, you only see these options:

| Option | What it does |
|--------|----------------|
| **Template theme** | Chooses how the prompt is built. Dropdown: **Dreamy / abstract**, **Lyrics + style**, **Music video still**, **Minimal** (lyrics only), **Song + artist**. Each preset is a different combination of `{lyrics}`, `{song}`, and `{artist}` — see the table below. |
| **Lyrics as keywords only** | **Off** (default): use the full lyric line. **On**: strip common words so the prompt is more keyword-like (e.g. “heart break run night”) for stronger visual cues. |
| **Style rotation interval (sec)** | **0** (default): the rotating style word (cinematic, dreamy, noir, etc.) changes only when the lyric line changes. **> 0** (e.g. 3): the style word advances every N seconds so the look changes more often even on the same line. |
| **Preview next line (sec)** | **0** (default): prompt uses the lyric line at the current playback position. **> 0** (e.g. 2): prompt uses the line that’s N seconds ahead so the image starts changing to the next line before it’s sung. |
| **Fallback Prompt** | Text used when no track is playing (default: “Abstract flowing colors and shapes”). |

**Built-in (no toggles):** The plugin always uses **time-synced lyrics** from **LRCLIB** and appends a **rotating style word** (cinematic, dreamy, noir, vivid, surreal, ethereal, dramatic, moody, luminous, atmospheric) so the prompt updates with the current line and varies in style. There are no options to turn lyrics or the style word off.

**Environment overrides (optional):** You can set `SPOTIFY_TEMPLATE_THEME`, `SPOTIFY_FALLBACK_PROMPT`, `SPOTIFY_LYRICS_KEYWORDS_ONLY`, `SPOTIFY_LYRICS_STYLE_ROTATION_SECONDS`, `SPOTIFY_LYRICS_PREVIEW_SECONDS` in the environment instead of or in addition to the UI.

### Template theme presets (how each is constructed)

Each preset builds the prompt from placeholders: `{song}` = track title, `{artist}` = artist name(s), `{lyrics}` = current time-synced lyric line (with rotating style word appended). Lyrics are always fetched and synced; if none are found for a track, `{lyrics}` is empty.

#### Comparison of prompt templates

| Theme | Template string | Uses lyrics? |
|-------|-----------------|--------------|
| **Dreamy / abstract** | `{lyrics}, dreamlike, {song} by {artist}, soft lighting` | Yes |
| **Lyrics + style** | `{lyrics}, inspired by {song} and {artist}, vivid` | Yes |
| **Music video still** | `Music video frame: {lyrics}, "{song}" by {artist}, cinematic` | Yes |
| **Minimal** | `{lyrics}` | Yes (only) |
| **Song + artist** | `{song} by {artist}, vivid, cinematic` | No |

#### Description (how each is built)

| Theme | Description | How the prompt is built |
|-------|-------------|-------------------------|
| **Dreamy / abstract** | Soft, dreamlike visuals driven by the current lyric line and song. | `{lyrics}, dreamlike, {song} by {artist}, soft lighting` — lyrics first, then song/artist, with “dreamlike” and “soft lighting” so the image model leans abstract and soft. |
| **Lyrics + style** | Lyrics drive the scene; song and artist add a vivid, inspired-by style. | `{lyrics}, inspired by {song} and {artist}, vivid` — lyric content as the main subject, with song/artist as style context. |
| **Music video still** | Single frame that could be from a music video for the track. | `Music video frame: {lyrics}, "{song}" by {artist}, cinematic` — frames the prompt as a music-video shot, cinematic look. |
| **Minimal** | Only the current lyric line; no song/artist in the prompt. | `{lyrics}` — prompt is just the lyric text (with rotating style word). |
| **Song + artist** | Template omits lyrics; good for simple, recognizable imagery. (Lyrics are still fetched; only the template doesn’t use `{lyrics}`.) | `{song} by {artist}, vivid, cinematic` — title and artist plus “vivid, cinematic”. |

### Lyrics (built-in)

The plugin **always** uses **time-synced lyrics** from **LRCLIB** (free, no API key) and a **rotating style word** (cinematic, dreamy, noir, vivid, etc.) so the prompt updates with the current line and varies in style. Choose a **Template theme** that includes `{lyrics}` (e.g. Dreamy / abstract, Minimal) so the image follows the words; or use **Song + artist** for a shorter prompt. If synced lyrics aren’t found for a track, `{lyrics}` is empty and the prompt uses song/artist only.

### Tuning: keywords, style rotation, preview

- **Lyrics as keywords only** — Reduces each line to keyword-like words (strips common words). The prompt becomes more visual (e.g. “heart break run night”).
- **Style rotation interval (sec)** — **0** = advance the style word when the lyric line changes; **> 0** (e.g. 3) = advance every N seconds so the prompt changes more often.
- **Preview next line (sec)** — When **> 0** (e.g. 2), the *next* lyric line is shown that many seconds early so the image transitions sooner.

Env vars (optional): `SPOTIFY_LYRICS_KEYWORDS_ONLY`, `SPOTIFY_LYRICS_STYLE_ROTATION_SECONDS`, `SPOTIFY_LYRICS_PREVIEW_SECONDS`.

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
