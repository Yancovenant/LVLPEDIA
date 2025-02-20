# LVLPEDIA
Listen to audio inside your pocket


### Development

#### 1. Backend Development
- Odoo Online SaaS 18 as platform and website builder.
- Models:
  - `x_novel` (stores novels).
  - `x_novel.episodes` (stores episodes, linked to `x_novel`).
  - `x_subscription_model` (stores subscription types).
  - `x_subscription_plan` (stores user subscriptions, tracks `x_active` boolean based on `start_date` and `end_date`).

#### 2. Feature Implementation
- **Novel Upload:**
  - Options planned: *Upload PDF*, *Upload Audio*, *Write Your Own Novel*.
  - **PDF Upload:**
    - Auto-generates audio and subtitles using **edge_tts**.
    - Uses **Flask** app on **Google Colab**/**local machine**, exposed via **Cloudflare Tunnel** (`api2.lvlpedia.space`).
    - Odoo Scheduled Action triggers API for generation.
  - **Audio Upload:**
    - Users upload audio files.
    - Subtitles generated via **Deepgram API** (with plans to move to a self-hosted solution).

- **Audio Player:**
  - Custom `<audio>` tag with container for controls.
  - Features: Play, Stop, Seekbar, Next/Prev Episode, Share, Like.
  - Offcanvas popup for expanded player (Spotify-inspired).
  - Goal: Continuous playback across page navigation.
  - Premium users can view full text; non-premium users see blurred overlay with membership prompt.
  - Planned: Bookmark feature to complement Like.

#### 3. UI/UX Design
- Basic prototype in place.
- Wireframing in progress (Spotify-inspired design).
- Pages to design:
  - Homepage
  - Novel Page
  - User Profile Page
  - Membership Page
  - Upload Novel Form

#### 4. Social & User Interaction
- **Session Tracking:** Recently viewed novels.
- **Like System:** Novels and episodes linked to `res.partner` via many2many fields.
- **Sharing:**
  - Functional: WhatsApp, Twitter, Facebook, URL copy.
  - In Development: Image sharing (Instagram Stories/Reels) via canvas-to-image conversion.
  - Current Issue: Maintaining consistent aspect ratio across devices.
- **User Profile Page:**
  - Users can share their profiles.

#### 5. Payment Integration
- Using **PayPal API** in sandbox mode.
- Manual payment processing (no recurring charges yet).
- Plans to add more payment gateways (future priority).

#### 6. External API Integration
- **Deepgram API:** For subtitle generation from uploaded audio (current but limited).
- **edge_tts:** For auto-generating audio from PDF text.
- Plan to self-host subtitle generation to avoid Deepgram limitations.

#### 7. Flask App Hosting
- Currently on **Google Colab**/**local machine**.
- Considering **Raspberry Pi** setup for efficient, continuous hosting.
- Concerns about performance yet to be tested.

### Child Sections

#### Wireframing
- **Status:** In Progress
- **Focus:**
  - Creating UI/UX wireframes for core and additional pages.
  - Inspired by Spotify's design language.
  - Addressing user flows, layouts, and feature placements.
- **Pages to Wireframe:**
  - Homepage
  - Novel Page
  - User Profile Page
  - Membership Page
  - Upload Novel Form
  - Additional Pages (as identified)
- **Next Steps:**
  - Awaiting user-provided sketches for review and refinement.

