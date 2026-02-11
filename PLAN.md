# Spotify Playlist Visual Generator - Project Plan

## Overview
Build a system that takes a Spotify playlist URL, extracts song information, and generates real-time AI visuals using Daydream that evolve based on the currently playing song. The project evolves from basic title-based visuals to a full companion visualizer app that syncs with Spotify playback.

### Project Phases at a Glance
| Phase | Focus | Key Feature |
|-------|-------|-------------|
| 1 | Song Title Visuals | MVP - Generate visuals from song titles |
| 2 | Lyrics Integration | Enhance prompts with song lyrics |
| 3 | Audio Features | Use Spotify's mood/energy data |
| 4 | Companion Visualizer | Full-screen app synced to Spotify |

---

## Phase 1: Song Title-Based Visuals (MVP)

### 1.1 Spotify Integration
- **Task**: Set up Spotify API authentication
- **Details**:
  - Register app on Spotify Developer Dashboard
  - Implement OAuth 2.0 flow for user authorization
  - Store access/refresh tokens securely

### 1.2 Playlist Parsing
- **Task**: Extract playlist data from Spotify
- **Details**:
  - Accept playlist URL/URI as input
  - Fetch all tracks in the playlist via Spotify Web API
  - Extract: song title, artist name, album name, duration, album art

### 1.3 Prompt Engineering
- **Task**: Convert song titles into visual prompts
- **Details**:
  - Create a prompt template that incorporates song title
  - Example: `"A dreamy, atmospheric visual inspired by the song '{title}' by {artist}, cinematic lighting, abstract art"`
  - Consider genre-based style modifiers (if available from Spotify)

### 1.4 Daydream Integration
- **Task**: Connect to Daydream AI for visual generation
- **Details**:
  - Start a stream session with initial prompt
  - Update prompt in real-time as songs change
  - Expose playback URL for viewing the visuals

### 1.5 Playback Synchronization
- **Task**: Sync visuals with song changes
- **Details**:
  - Track current song position in playlist
  - Trigger prompt update when song transitions
  - Handle play/pause/skip events (optional for MVP)

### Phase 1 Deliverables
- [ ] Working Spotify authentication
- [ ] Playlist URL input → song list extraction
- [ ] Real-time visual stream that changes per song title
- [ ] Playback URL to view the generated visuals

---

## Phase 2: Lyrics-Based Visuals (Enhancement)

### 2.1 Lyrics Fetching
- **Task**: Integrate a lyrics API
- **Options** (optional; currently using title/metadata only):
  - Musixmatch API
  - LyricsOVH (free, limited)
  - Other lyrics providers
- **Details**:
  - Match song title + artist to fetch correct lyrics
  - Handle songs without lyrics (instrumentals)
  - Cache lyrics to reduce API calls

### 2.2 Lyrics Processing
- **Task**: Extract meaningful visual prompts from lyrics
- **Options**:
  - **Simple**: Use chorus/hook section
  - **Advanced**: Use AI to summarize lyrics into visual themes
  - **Real-time**: Sync specific lines with playback position
- **Details**:
  - Parse lyrics into sections (verse, chorus, bridge)
  - Identify key imagery and emotions
  - Create time-stamped prompts for dynamic updates

### 2.3 Enhanced Prompt Generation
- **Task**: Combine title, artist, and lyrics into rich prompts
- **Details**:
  - Primary prompt from lyrics themes/imagery
  - Style modifiers from genre/artist vibe
  - Smooth transitions between lyric sections

### 2.4 Real-time Lyric Sync (Advanced)
- **Task**: Update visuals as lyrics progress
- **Options**:
  - Change prompt every verse/chorus
  - Change prompt every N seconds
  - Use Spotify's playback position API
- **Details**:
  - Requires time-synced lyrics (limited availability)
  - Fallback to section-based updates

### Phase 2 Deliverables
- [ ] Lyrics API integration
- [ ] Lyrics-to-visual prompt conversion
- [ ] Enhanced visuals that reflect song meaning
- [ ] (Optional) Real-time lyric synchronization

---

## Phase 3: Audio Feature Enhancement

### 3.1 Spotify Audio Features API
- **Task**: Fetch audio analysis data for each track
- **Details**:
  - Spotify provides: energy, valence (happiness), danceability, tempo, loudness, acousticness
  - These are numeric values (0.0 - 1.0) for each track
  - No Premium required - works with any track ID

### 3.2 Feature-to-Visual Mapping
- **Task**: Translate audio features into visual parameters
- **Mapping Examples**:
  | Audio Feature | Visual Effect |
  |---------------|---------------|
  | Energy (high) | Intense colors, fast movement, sharp edges |
  | Energy (low) | Soft pastels, slow drifts, smooth gradients |
  | Valence (happy) | Warm colors, bright lighting, upward motion |
  | Valence (sad) | Cool blues, shadows, downward/inward motion |
  | Danceability | Rhythmic patterns, geometric shapes |
  | Acousticness | Organic textures, natural elements |
  | Tempo (BPM) | Animation speed, transition pace |

### 3.3 Dynamic Prompt Modifiers
- **Task**: Inject audio features into prompt generation
- **Details**:
  - Base prompt from title/lyrics (Phase 1-2)
  - Add style modifiers based on audio features
  - Example: `"{base_prompt}, high energy, vibrant neon colors, fast-paced, electric atmosphere"`

### 3.4 Mood Transitions
- **Task**: Smooth visual transitions between songs with different moods
- **Details**:
  - Compare audio features between current and next song
  - Gradual parameter shifts during song transitions
  - Avoid jarring visual jumps

### Phase 3 Deliverables
- [ ] Audio features fetched for all playlist tracks
- [ ] Feature-to-visual mapping system
- [ ] Mood-aware prompt generation
- [ ] Smooth transitions between contrasting songs

---

## Phase 4: Companion Visualizer App

### 4.1 Real-time Spotify Sync
- **Task**: Connect to Spotify's Currently Playing API
- **Details**:
  - Poll Spotify every 1-2 seconds for playback state
  - Detect song changes, play/pause, seek events
  - Requires Spotify Premium for full playback control API
  - Handle offline/disconnected states gracefully

### 4.2 Full-Screen Visualizer UI
- **Task**: Build immersive web-based visualizer
- **Components**:
  ```
  ┌─────────────────────────────────────────────────────────────┐
  │                                                             │
  │                    [AI VISUAL STREAM]                       │
  │                    (Full Background)                        │
  │                                                             │
  │                                                             │
  ├─────────────────────────────────────────────────────────────┤
  │  🎵 Song Title - Artist                           advancement│
  │  ▶ advancement────────────────●────────────── 2:34 / 3:45    │
  │  [Album Art]  ❮❮  ▶/❚❚  ❯❯                      🔊 ━━━●━━  │
  └─────────────────────────────────────────────────────────────┘
  ```
- **Features**:
  - Daydream stream as full-screen background
  - Now Playing overlay (can be hidden)
  - Progress bar synced with Spotify
  - Minimal controls (or control from Spotify app)

### 4.3 Display Modes
- **Task**: Multiple viewing options
- **Modes**:
  - **Immersive**: Full-screen visuals only, no UI
  - **Now Playing**: Visuals + song info overlay
  - **Mini Player**: Small window/widget mode
  - **Ambient**: Slower, calmer visuals for background use

### 4.4 Second Screen Support
- **Task**: Enable "visualizer on TV/projector" use case
- **Details**:
  - Shareable URL for the visual stream
  - Cast/Chromecast support (stretch goal)
  - QR code to open on another device
  - Independent of Spotify app location

### Phase 4 Deliverables
- [ ] Real-time Spotify playback sync
- [ ] Full-screen web visualizer app
- [ ] Now Playing overlay with controls
- [ ] Multiple display modes
- [ ] Second screen/shareable URL support

---

## Technical Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Spotify API    │────▶│  Backend Server  │────▶│  Daydream AI    │
│  - Playlist     │     │  - Node.js/Python│     │  - Visual Gen   │
│  - Playback     │     │  - Prompt Engine │     │  - WHIP Stream  │
│  - Audio Feat.  │     │  - Sync Manager  │     │                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │                     │                        │
         │                     ▼                        │
         │              ┌──────────────────┐            │
         │              │  Lyrics API      │            │
         │              │  (Phase 2)       │            │
         │              └──────────────────┘            │
         │                     │                        │
         ▼                     ▼                        ▼
    ┌───────────────────────────────────────────────────────┐
    │              Companion Visualizer App                 │
    │  ┌─────────────────────────────────────────────────┐  │
    │  │            Full-Screen Visual Stream            │  │
    │  │                                                 │  │
    │  ├─────────────────────────────────────────────────┤  │
    │  │  Now Playing: Song - Artist         [Controls]  │  │
    │  └─────────────────────────────────────────────────┘  │
    └───────────────────────────────────────────────────────┘
```

## Tech Stack Recommendation

| Component | Technology | Reason |
|-----------|------------|--------|
| Backend | Node.js or Python | Good Spotify SDK support |
| Spotify SDK | spotify-web-api-node / spotipy | Official-like libraries |
| Lyrics API | Optional (Musixmatch, etc.) | Add later if needed |
| Visual Gen | Daydream MCP | Already integrated |
| Frontend | Simple HTML/React | Display stream + controls |

---

## Implementation Order

### Phase 1 (Weeks 1-2): Song Title Visuals
1. Set up project structure
2. Implement Spotify OAuth
3. Build playlist fetcher
4. Create prompt generation logic
5. Integrate Daydream streaming
6. Build basic UI to input playlist and view stream

### Phase 2 (Weeks 3-4): Lyrics Integration
7. (Optional) Integrate lyrics API
8. Build lyrics parser and theme extractor
9. Enhance prompt generation with lyrics
10. Add section-based visual transitions

### Phase 3 (Weeks 5-6): Audio Features
11. Fetch audio features from Spotify
12. Build feature-to-visual mapping system
13. Implement mood-aware prompts
14. Add smooth mood transitions

### Phase 4 (Weeks 7-8): Companion App
15. Implement Spotify playback sync
16. Build full-screen visualizer UI
17. Add Now Playing overlay
18. Create display modes (immersive, mini, ambient)
19. Enable second screen/shareable URL

---

## Questions to Clarify Before Starting

1. **Playback control**: Should visuals sync with actual Spotify playback, or just cycle through the playlist independently?

2. **Hosting**: Will this run locally or need to be deployed (affects auth flow)?

3. **UI preferences**: Minimal CLI-based, or web interface with controls?

4. **Spotify account**: Do you have Spotify Premium? (Required for some playback APIs)

5. **Lyrics priority**: For Phase 2, prefer real-time line-by-line sync or section-based (verse/chorus)?

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Spotify rate limits | Cache playlist data, batch requests |
| Lyrics not available | Fallback to title-based prompts |
| Prompt quality varies | Build prompt templates with consistent style anchors |
| Daydream stream interruptions | Auto-reconnect logic |
| Playback sync requires Premium | Graceful degradation to manual mode |
| Audio features unavailable for some tracks | Use genre/artist defaults |
| Spotify API changes | Abstract API calls for easy updates |

---

## Spotify Plugin Limitation Note

> **Why not a native Spotify plugin?**
>
> Spotify does not allow third-party visualizers inside their app. Their "Canvas" feature (looping visuals) is only available to verified artists. There is no public API for UI plugins or audio stream access.
>
> **Our solution**: A companion web app that syncs with Spotify playback via their API. This provides the same "visualizer" experience in a browser window, second screen, or projector.

---

## Next Steps

Once you approve this plan:
1. I'll start with Phase 1.1 (Spotify Integration)
2. Create the project structure
3. Guide you through Spotify Developer setup
4. Build incrementally with testing at each step

**Please review and let me know:**
- Any changes to the phases?
- Answers to the clarification questions?
- Ready to proceed?

---

## Future Possibilities (Not in Current Scope)

For reference, potential Phase 5+ features that could be added later:
- Multi-output support (OBS, video recording, live streaming)
- Chromecast/AirPlay integration
- Social features (shared sessions, community prompts)
- VJ mode for live performances
- Mobile app version
