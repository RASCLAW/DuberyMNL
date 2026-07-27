# youtube/

YouTube account write ops via the Data API v3, using the shared Google OAuth
token (`token.json`, already carries the `youtube` scope).

Read-only ops (video info, transcript, search, channel) live in the global
`/youtube` skill. This dir is for **writes** to RA's account.

| Script | Purpose |
|--------|---------|
| `create_playlist.py` | Create a playlist (private/unlisted/public) and optionally seed it with videos from URLs, bare IDs, or a file. |
| `gen_planco_player.py` | Build the local Planco 3D-roof video player HTML from a channel-uploads dump (`roof_channel_recent.json`). No API call, no account write. |

## create_playlist.py

```bash
# Empty private playlist
python tools/youtube/create_playlist.py "My Playlist"

# Full: description + visibility + seed videos (URLs or IDs)
python tools/youtube/create_playlist.py "Landcover Training" \
    --desc "Annotation reference clips" --privacy unlisted \
    --add https://youtu.be/ID1 ID2

# Seed from a file (one URL/ID per line, # comments ok)
python tools/youtube/create_playlist.py "Batch" --add-file videos.txt

# Preview without writing / spending quota
python tools/youtube/create_playlist.py "Test" --add URL --dry-run
```

- Accepts `watch?v=`, `youtu.be/`, `/shorts/`, `/embed/`, or bare 11-char IDs; dedupes.
- Quota: create = 50 units, each add = 50 units (10k/day budget).
- Failed video adds are reported per-line; the playlist is still created.

## gen_planco_player.py

```bash
python tools/youtube/gen_planco_player.py                     # defaults
python tools/youtube/gen_planco_player.py --data other.json --out custom.html
```

Reads `roof_channel_recent.json` (sibling of the script) and writes
`~/.config/media-players/planco-roof-player.html`, mirroring to
`~/Study/ryu/3droof/` if that folder exists. 38 videos from **Robbie Cian
Planco** (`UCGVIxKU8Nku89wlFLBbQW8Q`), grouped as a learning path with search
and localStorage watched-progress.

To refresh the data: re-pull the channel uploads via the YouTube Data API
(`YOUTUBE_API_KEY` in `.env`), filter to recent publishes, rewrite the JSON,
re-run. Study material itself lives at `~/Study/ryu/` (proprietary RYU content
— kept out of git, backed up to Drive).
