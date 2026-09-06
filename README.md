# 🎵 Soundcloud-Downloader-Bot

A clean, production-friendly Telegram bot built with **python-telegram-bot**, **yt-dlp**, and **FFmpeg**. Send a supported media URL and the bot downloads the best available audio, converts it to **MP3 320 kbps**, embeds available metadata/artwork, and sends it back through Telegram.

**Author:** [iArvin0](https://github.com/iArvin0)

> [فارسی](#فارسی) · [English](#english)

---

# English

## Features

- `python-telegram-bot` async architecture
- `yt-dlp[default]` media extraction
- FFmpeg conversion to **MP3 320 kbps**
- Supports URLs handled by yt-dlp, including SoundCloud and many other services
- Uses the best available source audio before conversion
- Embeds available metadata and cover artwork into MP3 files
- Sends title, artist, duration, source, output size, and quality in Telegram
- `/start` and `/help` commands
- No database
- No forced-channel membership
- Per-user active-download lock
- Configurable global concurrent-download limit
- Download progress/status messages
- Rotating file logs with full tracebacks for unexpected failures
- Automatic temporary-file cleanup
- Docker and Docker Compose support
- GitHub Actions lint + tests
- Environment-variable configuration

## Requirements

- Python **3.12+** recommended
- FFmpeg available in `PATH`
- A Telegram bot token from **@BotFather**

The Docker image installs FFmpeg automatically.

## Quick start

```bash
git clone https://github.com/iArvin0/Soundcloud-Downloader-Bot.git
cd Soundcloud-Downloader-Bot

python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows PowerShell

pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set your bot token:

```env
BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
```

Make sure FFmpeg is installed, then run:

```bash
python run.py
```

## Docker

```bash
cp .env.example .env
# Edit .env and set BOT_TOKEN

docker compose up -d --build
```

View live logs:

```bash
docker compose logs -f
```

Stop the bot:

```bash
docker compose down
```

## Windows FFmpeg

Install FFmpeg with WinGet:

```powershell
winget install -e --id Gyan.FFmpeg
```

Then **close and reopen PowerShell** and verify both executables are visible:

```powershell
ffmpeg -version
ffprobe -version
```

If FFmpeg is installed but not available in `PATH`, point the bot directly to the folder containing `ffmpeg.exe` and `ffprobe.exe`:

```env
FFMPEG_LOCATION=C:\path\to\ffmpeg\bin
```

The bot now detects missing FFmpeg before yt-dlp starts post-processing and returns a clean error instead of raw terminal control codes.

## Ubuntu / Debian FFmpeg

```bash
sudo apt update
sudo apt install -y ffmpeg
ffmpeg -version
```

## Configuration

| Variable | Default | Description |
|---|---:|---|
| `BOT_TOKEN` | required | Telegram Bot API token |
| `DOWNLOAD_DIR` | `downloads` | Temporary download directory |
| `LOG_DIR` | `logs` | Log directory |
| `MAX_CONCURRENT_DOWNLOADS` | `2` | Global simultaneous download limit |
| `TELEGRAM_MAX_FILE_MB` | `50` | Maximum output size the bot will try to upload |
| `FFMPEG_LOCATION` | empty | Optional directory containing `ffmpeg` and `ffprobe` when they are not in `PATH` |

MP3 quality is fixed at **320 kbps** in the application code as requested.

## Commands

| Command | Description |
|---|---|
| `/start` | Start/welcome message |
| `/help` | Usage information |

All other text messages are treated as URLs. The bot accepts only `http://` and `https://` URLs.

## How it works

1. The user sends a URL.
2. yt-dlp reads the media information and downloads the best available audio stream.
3. FFmpeg converts the audio to MP3 at a requested target bitrate of 320 kbps.
4. yt-dlp/FFmpeg embed available metadata and thumbnail artwork.
5. The bot checks the final output size.
6. The MP3 is uploaded with Telegram music-player metadata.
7. Temporary files are deleted whether the request succeeds or fails.

> Converting to 320 kbps does **not** increase the real quality of a source whose original bitrate/quality is lower.

## Telegram upload limit

The standard Telegram Bot API currently documents a **50 MB** limit for `sendAudio`. The bot checks the generated file before upload and returns a readable error instead of crashing when the output exceeds the configured limit.

At 320 kbps, long media can exceed this limit relatively quickly. This project intentionally does not silently reduce the requested bitrate.

## Logging & troubleshooting

Logs are written to:

```text
logs/bot.log
```

The logger rotates automatically:

- maximum ~5 MB per log file
- 5 backup files
- console + file output
- unexpected exceptions include traceback details

Useful checks:

```bash
python --version
ffmpeg -version
pip show python-telegram-bot yt-dlp
```

If a website suddenly stops working, first update yt-dlp because extractors change frequently:

```bash
pip install -U yt-dlp
```

If you use pinned dependencies in production, test the update and then update the pinned version in `requirements.txt`.

## Project structure

```text
Soundcloud-Downloader-Bot/
├── bot/
│   ├── __init__.py
│   ├── config.py
│   ├── downloader.py
│   ├── handlers.py
│   ├── logging_config.py
│   ├── main.py
│   └── utils.py
├── tests/
│   └── test_utils.py
├── .github/
│   └── workflows/
│       └── ci.yml
├── .dockerignore
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── LICENSE
├── README.md
├── requirements-dev.txt
├── requirements.txt
├── pyproject.toml
└── run.py
```

## Security notes

- Never commit your `.env` file or bot token.
- Rotate the token immediately in BotFather if it is leaked.
- The project does not attempt to bypass DRM, authentication, paywalls, or access controls.
- yt-dlp support depends on each website and can change over time.
- Run public downloader bots with sensible CPU, disk, bandwidth, and concurrency limits.

## Legal

Use this project only for media that you own, that is licensed for download, or that you otherwise have permission to download. You are responsible for complying with the terms of the source service and applicable law.

## License

MIT © 2026 [iArvin0](https://github.com/iArvin0)

---

# فارسی

این پروژه یک ربات کامل تلگرام برای دریافت لینک رسانه، دانلود بهترین صدای موجود با **yt-dlp**، تبدیل آن با **FFmpeg** به **MP3 با بیت‌ریت هدف 320 kbps** و ارسال فایل در تلگرام است. خود ربات کاملاً انگلیسی است و فقط این `README.md` به دو زبان نوشته شده است.

**توسعه‌دهنده:** [iArvin0](https://github.com/iArvin0)

## امکانات

- ساخته‌شده با `python-telegram-bot` و معماری Async
- دانلود رسانه با `yt-dlp`
- تبدیل صدا با FFmpeg به MP3 با کیفیت هدف `320 kbps`
- پشتیبانی از لینک‌هایی که yt-dlp پشتیبانی می‌کند؛ از جمله SoundCloud و سرویس‌های متعدد دیگر
- دانلود بهترین منبع صوتی موجود قبل از تبدیل
- قراردادن Metadata و تصویر کاور در فایل MP3 در صورت موجود بودن
- نمایش نام آهنگ، Artist، مدت، منبع، حجم و کیفیت خروجی
- فقط دو دستور `/start` و `/help`
- بدون SQL و بدون دیتابیس
- بدون عضویت اجباری کانال
- جلوگیری از چند دانلود همزمان توسط یک کاربر
- محدودیت قابل تنظیم برای تعداد دانلودهای همزمان کل بات
- نمایش وضعیت دانلود و تبدیل
- سیستم Log چرخشی برای پیدا کردن خطاها
- ثبت Traceback کامل خطاهای غیرمنتظره
- حذف خودکار فایل‌های موقت
- Docker و Docker Compose
- تست و Lint با GitHub Actions
- تنظیمات امن با فایل `.env`

## پیش‌نیازها

- پیشنهاد: Python `3.12+`
- FFmpeg
- توکن ربات از `@BotFather`

در نسخه Docker، FFmpeg به‌صورت خودکار نصب می‌شود.

## نصب معمولی

```bash
git clone https://github.com/iArvin0/Soundcloud-Downloader-Bot.git
cd Soundcloud-Downloader-Bot

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

حالا فایل `.env` را باز کن و توکن را قرار بده:

```env
BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
```

سپس:

```bash
python run.py
```

### نصب FFmpeg روی Windows

در PowerShell اجرا کن:

```powershell
winget install -e --id Gyan.FFmpeg
```

بعد **PowerShell را کامل ببند و دوباره باز کن** و این دو دستور را تست کن:

```powershell
ffmpeg -version
ffprobe -version
```

اگر FFmpeg نصب است ولی داخل `PATH` دیده نمی‌شود، مسیر پوشه‌ای که `ffmpeg.exe` و `ffprobe.exe` داخل آن هستند را در `.env` قرار بده:

```env
FFMPEG_LOCATION=C:\path\to\ffmpeg\bin
```

خطاهای شناخته‌شده مثل نبودن FFmpeg و DRM حالا به‌صورت پیام تمیز و قابل‌فهم در تلگرام نمایش داده می‌شوند.

### نصب FFmpeg روی Ubuntu/Debian

```bash
sudo apt update
sudo apt install -y ffmpeg
```

## اجرا با Docker

```bash
cp .env.example .env
# BOT_TOKEN را داخل .env تنظیم کن

docker compose up -d --build
```

دیدن لاگ‌ها:

```bash
docker compose logs -f
```

خاموش کردن:

```bash
docker compose down
```

## تنظیمات `.env`

| متغیر | مقدار پیش‌فرض | توضیح |
|---|---:|---|
| `BOT_TOKEN` | اجباری | توکن ربات تلگرام |
| `DOWNLOAD_DIR` | `downloads` | مسیر فایل‌های موقت |
| `LOG_DIR` | `logs` | مسیر لاگ‌ها |
| `MAX_CONCURRENT_DOWNLOADS` | `2` | تعداد دانلود همزمان کل بات |
| `TELEGRAM_MAX_FILE_MB` | `50` | بیشترین حجمی که بات برای آپلود تلاش می‌کند |
| `FFMPEG_LOCATION` | خالی | مسیر اختیاری پوشه `ffmpeg` و `ffprobe` وقتی در `PATH` نیستند |

کیفیت MP3 طبق درخواست روی **320 kbps** ثابت شده است.

## دستورات بات

```text
/start
/help
```

هر پیام متنی دیگر به‌عنوان URL بررسی می‌شود. فقط لینک‌های `http://` و `https://` پذیرفته می‌شوند.

## روند کار

1. کاربر لینک را برای ربات می‌فرستد.
2. yt-dlp اطلاعات رسانه را دریافت می‌کند.
3. بهترین Audio موجود دانلود می‌شود.
4. FFmpeg آن را به MP3 با بیت‌ریت هدف 320 kbps تبدیل می‌کند.
5. Metadata و کاور موجود داخل MP3 قرار می‌گیرد.
6. حجم فایل بررسی می‌شود.
7. فایل به شکل Audio در پلیر تلگرام ارسال می‌شود.
8. فایل‌های موقت در پایان پاک می‌شوند.

**نکته:** اگر کیفیت فایل اصلی پایین‌تر باشد، تبدیل آن به 320 kbps کیفیت واقعی صدا را بیشتر نمی‌کند.

## محدودیت حجم تلگرام

Telegram Bot API استاندارد در حال حاضر برای `sendAudio` حداکثر **50 MB** را مستند کرده است. بات قبل از آپلود حجم فایل را بررسی می‌کند؛ اگر فایل بزرگ‌تر باشد، به‌جای Crash کردن یک پیام خطای مشخص می‌دهد و موضوع در Log ثبت می‌شود.

بات کیفیت را به‌صورت مخفیانه پایین نمی‌آورد چون خروجی 320 kbps خواسته شده است.

## سیستم Log و پیدا کردن خطا

فایل اصلی لاگ:

```text
logs/bot.log
```

ویژگی‌ها:

- ثبت همزمان در Console و فایل
- چرخش Log در حدود 5MB
- نگهداری 5 فایل Backup
- ثبت Traceback کامل برای خطاهای غیرمنتظره
- ثبت درخواست‌ها، خطاهای yt-dlp و خطاهای آپلود

برای بررسی سریع:

```bash
python --version
ffmpeg -version
pip show python-telegram-bot yt-dlp
```

اگر سایتی قبلاً کار می‌کرد و ناگهان دانلود آن خراب شد، احتمال دارد extractor آن سایت تغییر کرده باشد. در این حالت معمولاً اولین کار آپدیت yt-dlp است:

```bash
pip install -U yt-dlp
```

## ساختار پروژه

```text
Soundcloud-Downloader-Bot/
├── bot/
│   ├── __init__.py
│   ├── config.py
│   ├── downloader.py
│   ├── handlers.py
│   ├── logging_config.py
│   ├── main.py
│   └── utils.py
├── tests/
│   └── test_utils.py
├── .github/workflows/ci.yml
├── .dockerignore
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── LICENSE
├── README.md
├── requirements-dev.txt
├── requirements.txt
├── pyproject.toml
└── run.py
```

## امنیت

- فایل `.env` و توکن ربات را داخل GitHub قرار نده.
- اگر توکن لو رفت، فوراً آن را از BotFather عوض کن.
- این پروژه DRM، لاگین، Paywall یا محدودیت دسترسی سرویس‌ها را دور نمی‌زند.
- قابلیت دانلود هر سایت وابسته به پشتیبانی yt-dlp است و ممکن است با تغییر سایت نیاز به آپدیت yt-dlp باشد.
- اگر بات عمومی است، محدودیت CPU، فضای دیسک، پهنای باند و تعداد دانلود همزمان را جدی بگیر.

## استفاده قانونی

فقط محتوایی را دانلود کن که مالک آن هستی، اجازه دانلود آن را داری یا مجوز آن چنین استفاده‌ای را مجاز کرده است. مسئولیت رعایت قوانین و شرایط سرویس منبع با اجراکننده و کاربران بات است.

## لایسنس

MIT © 2026 [iArvin0](https://github.com/iArvin0)
