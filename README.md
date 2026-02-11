# Scope Spotify Plugin (minimal)

This plugin lets Scope **generate an image from whatever song is playing in Spotify**. It reads the current track (song title + artist), turns it into a prompt, and your image pipeline (e.g. Stream Diffusion) creates the image.

---

## What you need to do (in order)

1. **Create a Spotify app** (one-time) and copy your Client ID and Client Secret.
2. **Install the plugin in Scope** (paste the plugin URL in Scope’s plugin settings).
3. **Tell the plugin your credentials** (Client ID and Secret) where Scope runs — e.g. in RunPod’s dashboard or via env vars.
4. **Log in to Spotify once** on the machine where Scope runs (run the auth script, open a URL in your browser, paste the redirect back).
5. **In Scope:** set Pipeline to Stream Diffusion, Preprocessor to Spotify Prompt Generator, play a song in Spotify, then press **Play**.

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

The plugin needs your **Client ID** and **Client Secret** on the same machine (or pod) where Scope is running.

**If you use RunPod (or a similar cloud host):**

- Many hosts have an **Environment** or **Secrets** section in the pod/dashboard where you can add variables **without using the terminal**. Look for something like “Environment variables”, “Pod configuration”, or “Secrets”.
- Add two entries:
  - Name: `SPOTIFY_CLIENT_ID`   → Value: your Client ID
  - Name: `SPOTIFY_CLIENT_SECRET` → Value: your Client Secret
- Save and restart the pod if it’s already running.

**If you have to use the terminal:**  
“Export” just means “set this value for the current session.” Run these two lines (replace the placeholders with your real Client ID and Secret):

```bash
export SPOTIFY_CLIENT_ID="paste_your_client_id_here"
export SPOTIFY_CLIENT_SECRET="paste_your_client_secret_here"
```

---

## Step 4: One-time Spotify login (auth script)

The plugin needs a **one-time login** to your Spotify account on the machine where Scope runs (e.g. your RunPod). After that, it reuses the saved token.

**On RunPod:**

1. Open the **web terminal** (or SSH) for your pod.
2. The auth script lives in the **plugin repo**. If the repo isn’t on the pod yet, run:
   ```bash
   cd /app
   git clone https://github.com/Shih-Yu/Spotify_Scope_Plugin.git
   cd Spotify_Scope_Plugin/scope-spotify
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

1. In Scope, set **Pipeline** to **Stream Diffusion** (or your chosen image pipeline).
2. Set **Preprocessor** to **Spotify Prompt Generator**.
3. In the Spotify app on your phone or computer, **start playing a song** (same account you used in Step 4).
4. In Scope, press **Play**. The plugin will read the current track and send a prompt like “Artistic visualization of [song] by [artist]” to the pipeline, which will generate the image.

You won’t see the song name in Scope’s UI; the prompt is used internally when you press Play.

**If the prompt still shows something like “A 3D animated scene. A panda” instead of your song:**  
Scope may be showing the text you typed in the Prompts box instead of the preprocessor’s output. Try **clearing the Prompts box** (leave it empty) and press Play again — then the only prompt source is the Spotify preprocessor. If it still doesn’t change, check the **server logs** on the pod: look for `Spotify preprocessor: prompt from track: [song] by [artist]` (success) or `Spotify preprocessor: no track playing or API failed` (credentials/token issue). That will show whether the preprocessor ran and got the current track.

---

## If something doesn’t work

- **Plugin not installed:** Make sure you added the plugin URL in Scope (Step 2) and that Scope finished installing it.
- **“Nothing happens” when I press Play:** Restart Scope (or the pod) after Step 4 so it can load the token. Check that you ran the auth script **on the same pod** where Scope runs and that credentials (Step 3) are set there too.
- **RunPod: “python: command not found”:** Use `python3` instead of `python` (e.g. `python3 scripts/spotify_auth.py`).

---

## Optional: change the prompt text

Default prompt: *“Artistic visualization of [song] by [artist]”*.  

If your host lets you set more environment variables, you can add:

- `SPOTIFY_PROMPT_TEMPLATE` — e.g. `My style: {song} by {artist}` (must include `{song}` and `{artist}`).
- `SPOTIFY_FALLBACK_PROMPT` — used when no song is playing (default: “Abstract flowing colors and shapes”).

---

## License

MIT.
