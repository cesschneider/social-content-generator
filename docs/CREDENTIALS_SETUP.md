# Credentials Setup Guide

Step-by-step instructions for every API key and OAuth token the pipeline requires. Work through these in order — some services (Instagram, TikTok) require app review that takes days.

---

## 1. Anthropic (Claude API)

**Enables:** All text generation (LinkedIn, YouTube, TikTok, Instagram, X, Substack)

**Setup:**
1. Go to https://console.anthropic.com
2. Create an account or sign in
3. Navigate to **API Keys** → **Create Key**
4. Copy the key immediately (shown only once)

**Env vars:**
```
ANTHROPIC_API_KEY=sk-ant-...
```

**Gotchas:** Free tier has rate limits. For production use, add a payment method and request increased limits via the console.

---

## 2. Notion

**Enables:** Reading the 30-day content calendar

**Setup:**
1. Go to https://www.notion.so/my-integrations → **New Integration**
2. Name it (e.g., "Content Pipeline"), select your workspace, grant **Read content** permission
3. Copy the **Internal Integration Token** (starts with `secret_`)
4. Open your content calendar database in Notion → click **...** (top right) → **Add connections** → select your integration
5. Copy the database ID from the URL: `notion.so/{workspace}/{DATABASE_ID}?v=...`

**Env vars:**
```
NOTION_API_KEY=secret_...
NOTION_CALENDAR_DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Gotchas:** Database ID is the 32-char hex string in the URL, not the view ID after `?v=`. If the query returns 0 results, check that the integration is connected to the database (step 4).

---

## 3. HeyGen

**Enables:** AI avatar talking-head video generation

**Setup:**
1. Create an account at https://app.heygen.com
2. Go to **Account** → **API** → **Generate API Key**
3. Copy the API key
4. In the HeyGen studio, go to **Avatars** and note your preferred avatar's ID (shown in the URL or avatar details)
5. Go to **Voices** → select a voice → note the Voice ID

**Env vars:**
```
HEYGEN_API_KEY=...
HEYGEN_AVATAR_ID=...
HEYGEN_VOICE_ID=...
```

**Gotchas:** HeyGen video generation takes 5–15 minutes per video. The pipeline polls every 15 seconds up to 10 minutes. The script is truncated at 5,000 characters per HeyGen's limit — keep YouTube scripts concise or split into segments. Credits are consumed per video minute generated.

---

## 4. HuggingFace

**Enables:** FLUX image generation for Instagram carousel slides

**Setup:**
1. Create an account at https://huggingface.co
2. Go to **Settings** → **Access Tokens** → **New token**
3. Select **Read** role, name it, copy the token
4. (Optional) Request access to `black-forest-labs/FLUX.1-dev` at https://huggingface.co/black-forest-labs/FLUX.1-dev — it requires accepting the license

**Env vars:**
```
HUGGINGFACE_API_KEY=hf_...
```

**Gotchas:** FLUX.1-dev requires gated access — request it and wait for approval (usually instant). The free Inference API has rate limits; for production, use a dedicated Inference Endpoint or upgrade to PRO.

---

## 5. Higgsfield

**Enables:** Cinematic B-roll video clips

**Setup:**
1. Sign up at https://higgsfield.ai
2. Navigate to **API** or **Settings** → generate an API key
3. Copy the bearer token

**Env vars:**
```
HIGGSFIELD_API_KEY=...
```

**Gotchas:** Higgsfield is an early-stage API — check their docs for current endpoint URLs, as these may change. Jobs time out after 5 minutes in the pipeline. B-roll generation is optional; the pipeline skips it gracefully if the key is missing.

---

## 6. ElevenLabs

**Enables:** Text-to-speech voiceover for video overlays

**Setup:**
1. Create an account at https://elevenlabs.io
2. Go to **Profile** → **API Key** → copy the key
3. Go to **Voice Library**, choose or clone a voice, copy its **Voice ID** from the URL or voice settings

**Env vars:**
```
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID=...
```

**Gotchas:** Free tier allows ~10,000 characters/month. The `eleven_multilingual_v2` model produces the highest quality output but is slower. Voice cloning requires the Creator plan or above.

---

## 7. Canva (optional)

**Enables:** Branded template-based image generation (alternative to FLUX)

**Setup:**
1. Go to https://www.canva.com/developers → Apply for API access
2. Once approved, create an app and get a Client ID + Client Secret
3. Use the Brand Kit API to access your brand templates

**Env vars:** (add to `.env` as needed when integrating)
```
CANVA_CLIENT_ID=...
CANVA_CLIENT_SECRET=...
```

**Gotchas:** Canva API access requires application and approval. As of 2024, the Connect API is in limited beta. The pipeline uses HuggingFace FLUX by default; Canva integration would require a custom `image_gen.py` branch.

---

## 8. Cloudinary

**Enables:** Asset hosting — all media (video, images) must pass through Cloudinary before social API submission

**Setup:**
1. Sign up at https://cloudinary.com (free tier: 25GB storage, 25GB bandwidth/month)
2. From the **Dashboard**, copy your **Cloud Name**, **API Key**, and **API Secret**

**Env vars:**
```
CLOUDINARY_CLOUD_NAME=...
CLOUDINARY_API_KEY=...
CLOUDINARY_API_SECRET=...
```

**Gotchas:** Cloudinary `resource_type="auto"` is used for upload — it detects video vs. image automatically. Video uploads from remote URLs (HeyGen output) may take 30–60 seconds to process. Ensure your Cloudinary plan supports video if you're uploading MP4s (free tier does support it).

---

## 9. YouTube Data API v3

**Enables:** Video upload and metadata setting on YouTube

**Setup:**
1. Go to https://console.cloud.google.com → create a new project
2. Enable **YouTube Data API v3** in **APIs & Services** → **Library**
3. Go to **OAuth consent screen** → configure (External, add your email as test user)
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID** → **Desktop app**
5. Download the JSON file → save as `credentials/youtube_client_secret.json`
6. Run `python -m pipeline.auth.setup --platform youtube` — a browser window opens; sign in and grant access
7. Token is saved to `credentials/youtube_token.json`

**Env vars:**
```
YOUTUBE_CLIENT_SECRET_FILE=credentials/youtube_client_secret.json
YOUTUBE_TOKEN_FILE=credentials/youtube_token.json
```

**Gotchas:** YouTube API v3 imposes a 10,000 unit/day quota by default. Each video upload costs ~1,600 units. Submit a quota increase request if running daily. OAuth tokens expire after 1 hour but are auto-refreshed by the Google client library. The app stays in "test" mode until you submit for verification (required if publishing beyond 100 test users).

---

## 10. LinkedIn Marketing API

**Enables:** Publishing long-form posts to your LinkedIn profile

**Setup:**
1. Go to https://www.linkedin.com/developers/apps → **Create App**
2. Associate the app with a LinkedIn Page (create one if needed)
3. Under **Products**, request **Share on LinkedIn** and **Sign In with LinkedIn using OpenID Connect**
4. Wait for product approval (usually instant for Share on LinkedIn)
5. Go to **Auth** → copy **Client ID** and **Client Secret**
6. Run `python -m pipeline.auth.setup --platform linkedin`
7. Copy your access token from the output, and get your Person URN:
   - Make a GET request: `curl -H "Authorization: Bearer {token}" https://api.linkedin.com/v2/userinfo`
   - Your URN is `urn:li:person:{sub_value}` from the response

**Env vars:**
```
LINKEDIN_CLIENT_ID=...
LINKEDIN_CLIENT_SECRET=...
LINKEDIN_ACCESS_TOKEN=...
LINKEDIN_PERSON_URN=urn:li:person:xxxxxxxxxx
```

**Gotchas:** LinkedIn OAuth tokens expire in 60 days (or 2 months). There is no refresh token for the Marketing API — you must re-run the setup CLI every ~55 days. Set a calendar reminder. The `w_member_social` scope is required for posting.

---

## 11. Instagram Graph API

**Enables:** Publishing carousel posts and reels to a business Instagram account

**Setup:**
1. Your Instagram account must be a **Business** or **Creator** account, connected to a Facebook Page
2. Go to https://developers.facebook.com → create an app (**Business** type)
3. Add **Instagram Graph API** product to the app
4. Go to **App Review** → request `instagram_content_publish` permission (requires review — submit early, takes 1–5 business days)
5. While in development, add your Instagram account as a **Test User** in **Roles**
6. Go to **Tools** → **Graph API Explorer** → generate a User Access Token with `instagram_content_publish` scope
7. Exchange for a **Long-Lived Token** (valid 60 days):
   ```
   GET https://graph.facebook.com/oauth/access_token
     ?grant_type=fb_exchange_token
     &client_id={app_id}
     &client_secret={app_secret}
     &fb_exchange_token={short_lived_token}
   ```
8. Get your Instagram Business Account ID:
   ```
   GET https://graph.facebook.com/v19.0/me/accounts?access_token={token}
   ```
   Then: `GET /{page_id}?fields=instagram_business_account&access_token={token}`

**Env vars:**
```
INSTAGRAM_ACCESS_TOKEN=...
INSTAGRAM_BUSINESS_ACCOUNT_ID=...
```

**Gotchas:** Instagram carousel publishing requires minimum 2, maximum 10 images. Each image must be a publicly accessible HTTPS URL (use Cloudinary). App review for `instagram_content_publish` is required before you can publish from non-test accounts — submit the review as your first step since it can take days.

---

## 12. TikTok Content Posting API

**Enables:** Uploading and publishing videos to TikTok

**Setup:**
1. Go to https://developers.tiktok.com → **Manage Apps** → **Create App**
2. Under **Products**, add **Content Posting API**
3. Submit for **App Review** with justification (takes 3–7 business days — do this first)
4. Once approved, copy your **Client Key** and **Client Secret** from the app settings
5. Run `python -m pipeline.auth.setup --platform tiktok` — opens browser for PKCE flow
6. Tokens are saved to `credentials/tiktok_token.json`

**Env vars:**
```
TIKTOK_CLIENT_KEY=...
TIKTOK_CLIENT_SECRET=...
TIKTOK_ACCESS_TOKEN=    # auto-populated after auth setup
TIKTOK_REFRESH_TOKEN=   # auto-populated after auth setup
```

**Gotchas:** TikTok access tokens expire in **24 hours**. The pipeline auto-refreshes using the stored refresh token (valid 365 days). If the refresh token also expires, re-run the auth setup CLI. TikTok requires video to be at least 3 seconds and in MP4 or WebM format. `PULL_FROM_URL` source requires a publicly accessible HTTPS URL — Cloudinary handles this.

---

## 13. X API v2

**Enables:** Posting tweet threads via OAuth 1.0a

**Setup:**
1. Go to https://developer.twitter.com/en/portal/projects-and-apps → **Create App** (requires applying for Basic access, $100/month, or use a legacy free app if you have one)
2. Under **User authentication settings**, enable **OAuth 1.0a**, set permissions to **Read and Write**
3. Go to **Keys and Tokens**:
   - Copy **API Key** and **API Secret** (Consumer Keys)
   - Generate **Access Token** and **Access Token Secret** (make sure they have Write permissions)

**Env vars:**
```
TWITTER_API_KEY=...
TWITTER_API_SECRET=...
TWITTER_ACCESS_TOKEN=...
TWITTER_ACCESS_TOKEN_SECRET=...
```

**Gotchas:** The free X API tier (v2) allows 1,500 tweets/month — a 6-tweet thread daily uses ~180 tweets/month, well within limits. The Basic plan ($100/month) includes 3,000 tweets/month. OAuth 1.0a tokens do not expire. If you regenerate them in the developer portal, update `.env` immediately.

---

## 14. Substack / Ghost

**Enables:** Creating newsletter article drafts

### Option A — Substack

**Setup:**
1. Go to your Substack publication settings → **Publishing** → **API** (may require enabling in settings)
2. Generate an API key
3. Note your publication URL (e.g., `https://yourpub.substack.com`)

**Env vars:**
```
SUBSTACK_API_KEY=...
SUBSTACK_PUBLICATION_URL=https://yourpub.substack.com
```

**Gotchas:** Substack's API is unofficial and undocumented. The pipeline creates drafts via `POST /api/v1/posts`. This endpoint may change. Consider Ghost as the more stable alternative.

### Option B — Ghost (recommended)

**Setup:**
1. Set up a Ghost instance (Ghost Pro at https://ghost.org, or self-hosted)
2. In Ghost Admin → **Settings** → **Integrations** → **Add custom integration**
3. Name it, copy the **Admin API Key** (format: `key_id:key_secret`)
4. Note your Ghost URL (e.g., `https://yoursite.ghost.io`)

**Env vars:**
```
GHOST_ADMIN_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxx:yyyyyyyyyyyyyyyyyyyy...
GHOST_API_URL=https://yoursite.ghost.io
```

**Gotchas:** The pipeline detects Ghost automatically if `GHOST_ADMIN_API_KEY` is set; it takes priority over Substack. Ghost Admin API tokens are self-signed JWTs valid for 5 minutes — the publisher generates a fresh one per request. No token storage or refresh needed.

---

## Quick Checklist

| Service | Status | Time to set up | Notes |
|---|---|---|---|
| Anthropic | Instant | 5 min | Add payment for higher limits |
| Notion | Instant | 10 min | Must connect integration to database |
| HeyGen | Instant | 5 min | Credits consumed per minute of video |
| HuggingFace | ~1 hour | 10 min | FLUX gated model access |
| Higgsfield | Instant | 5 min | Early-access API |
| ElevenLabs | Instant | 5 min | Free tier: 10k chars/month |
| Cloudinary | Instant | 5 min | Free tier sufficient for testing |
| YouTube | 30 min | 30 min | OAuth + quota increase request |
| LinkedIn | ~1 day | 20 min | Product approval + 60-day token expiry |
| Instagram | 1–5 days | 30 min | App review required — submit first |
| TikTok | 3–7 days | 30 min | App review required — submit first |
| X / Twitter | Instant* | 15 min | *If you have existing dev access |
| Substack | Instant | 5 min | Unofficial API |
| Ghost | Instant | 10 min | Requires Ghost instance |

**Recommended order:** Start with Anthropic, Cloudinary, and Notion to run dry-run tests. Submit Instagram and TikTok app reviews on Day 1 since they take the longest.
