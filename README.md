# REimaginehome Content Creator

A Streamlit-based content creation dashboard for generating video scripts from blog articles and managing social media publishing.

## Features

- 📝 **Script Generation**: Generate video scripts from blog URLs using AI
- 🎬 **Video Management**: Upload and manage videos with metadata
- 📺 **Social Media Publishing**: Publish to YouTube, Instagram, TikTok, and Reimaginehome TV
- 🔐 **User Authentication**: Email-based login with shared password
- ⚙️ **Settings Management**: Configure API keys and master prompts
- 📊 **Analytics**: Track token usage, costs, and video statistics

## Quick Start

### Local Development

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Run the app**:
```bash
streamlit run app.py
```

3. **Configure environment variables**:
   - Copy `.env.example` to `.env`
   - Add your OpenAI API key (required) and any other platform credentials
   - You can also update keys from the in-app Settings → API Keys tab (values are written back to `.env`)

4. **Login**:
   - Use any email address
   - Use the shared password (default: `admin123`)

### Deploy to Streamlit Cloud

**Quick Start**: See [STREAMLIT_CLOUD_QUICK_START.md](STREAMLIT_CLOUD_QUICK_START.md) for a 3-step deployment guide.

**Full Guide**: See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed step-by-step instructions.

**Secrets Template**: See [.streamlit/secrets.toml.example](.streamlit/secrets.toml.example) for the required format.

## Project Structure

```
REimaginehome Content Creator/
├── app.py                 # Main application entry point
├── auth.py                # Authentication module
├── config.py              # Configuration and API key management
├── requirements.txt       # Python dependencies
├── .env.example           # Sample environment variables
├── .gitignore             # Git ignore rules
├── database/
│   └── db_setup.py        # Database initialization
├── pages/
│   ├── generate_scripts_page.py   # Script generation page
│   ├── upload_video_page.py       # Video upload and publishing
│   ├── video_management_page.py   # Video management
│   ├── settings_page.py           # Settings and configuration
│   ├── blog_url_page.py           # Helper for single-script retries
│   └── youtube_callback.py        # OAuth callback handler
├── integrations/
│   ├── youtube_api_v2.py  # YouTube API integration
│   ├── instagram_api.py   # Instagram API integration
│   ├── tiktok_api.py      # TikTok API integration
│   └── reimaginehome_tv_api.py  # Reimaginehome TV API
└── utils/
    ├── script_generator.py         # AI script generation
    ├── cloudinary_storage.py       # Media storage helpers
    ├── social_media_publisher.py   # Publishing helpers
    ├── video_frame_extractor.py    # Frame extraction utilities
    └── script_metadata_extractor.py  # Metadata extraction
```

## Configuration

### API Keys

API keys can be configured in two ways:

1. **Local Development**: Copy `.env.example` to `.env` and add your credentials (file is excluded from Git).
2. **Streamlit Cloud**: Add secrets in App Settings → Secrets. See [.streamlit/secrets.toml.example](.streamlit/secrets.toml.example) for the format.

The app automatically prioritizes:
- **Streamlit Secrets** (when running on Streamlit Cloud)
- **Environment Variables** (from `.env` file for local development)

### Master Prompts

Create and manage multiple master prompts in Settings → Master Prompt. The active prompt is used for script generation.

## Authentication

- **Email**: Any valid email address
- **Password**: Shared password (default: `admin123`, can be changed in Settings)
- **Session**: Persists until logout

## Database

The app uses **MongoDB** for data storage. 

- **Local Development**: Set `MONGO_URI` and `MONGO_DB_NAME` in your `.env` file
- **Streamlit Cloud**: Add MongoDB credentials in Streamlit Secrets under `[MongoDB]` section

Get your MongoDB connection string from [MongoDB Atlas](https://cloud.mongodb.com/).

## Deployment

### Streamlit Cloud (Recommended)

1. Push your code to GitHub
2. Deploy on [share.streamlit.io](https://share.streamlit.io)
3. Add secrets in App Settings → Secrets
4. See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for complete instructions

### Other Platforms

Set the same environment variables (or platform-specific secrets) before running `streamlit run app.py`.

## Requirements

- Python 3.8+
- Streamlit 1.28.0+
- OpenAI API key
- (Optional) YouTube, Instagram, TikTok API credentials

## License

Private project - All rights reserved

## Support

For issues or questions, check the deployment guides or contact the development team.
