# Cloudinary Integration Setup Guide

## Overview
Your Django project is now configured to use Cloudinary for image storage and management. This replaces local file storage with cloud-based storage, making your application more scalable and production-ready.

## What Was Changed

### 1. **Settings Configuration**
- Added `cloudinary_storage` to `INSTALLED_APPS`
- Configured Cloudinary API credentials
- Set `DEFAULT_FILE_STORAGE` to use Cloudinary as the media storage backend

### 2. **Model Updates**
Updated the following models to use `CloudinaryField`:
- **User** model: `profile_image` field
- **Room** model: `image` field

### 3. **Dependencies**
- Installed `django-cloudinary-storage` package

## Setup Instructions

### Step 1: Get Cloudinary Credentials

1. Go to [Cloudinary](https://cloudinary.com) and create a free account
2. Navigate to your **Dashboard**
3. You'll see your credentials:
   - Cloud Name
   - API Key
   - API Secret

### Step 2: Configure Environment Variables

1. Create a `.env` file in your project root (same level as `manage.py`)
2. Copy from `.env.example` and fill in your Cloudinary credentials:

```
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

**Important**: Never commit `.env` to version control. Add it to `.gitignore`.

### Step 3: Create and Run Migrations

If you've added new image fields or made changes, create and apply migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 4: Test the Integration

You can test Cloudinary integration by:

1. Creating a user with a profile image
2. Creating a room with an image
3. Checking your Cloudinary dashboard to see uploaded files

Example API call:
```bash
curl -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: multipart/form-data" \
  -F "username=testuser" \
  -F "profile_image=@/path/to/image.jpg"
```

## Features

✅ **Automatic uploads** - Images are automatically uploaded to Cloudinary  
✅ **URL generation** - Get direct URLs to images from Cloudinary  
✅ **Image optimization** - Cloudinary handles image compression and format conversion  
✅ **Responsive images** - Generate multiple sizes for different devices  
✅ **CDN delivery** - Global distribution through Cloudinary's CDN  

## Advanced Usage

### Transforming Images in Templates/Serializers

You can apply Cloudinary transformations to images:

```python
# In serializers or templates
image_url = instance.profile_image.build_url(
    width=300,
    height=300,
    crop='fill',
    quality='auto',
    fetch_format='auto'
)
```

### Available Transformations
- `width`, `height`: Resize dimensions
- `crop`: 'fill', 'fit', 'scale', 'crop'
- `quality`: 'auto', or quality level (1-100)
- `fetch_format`: 'auto', 'jpg', 'png', 'webp'
- `radius`: Add rounded corners

## Troubleshooting

### Images not uploading?
- ✓ Verify Cloudinary credentials in `.env`
- ✓ Check that `cloudinary_storage` is in `INSTALLED_APPS`
- ✓ Run migrations: `python manage.py migrate`

### Getting "API key not provided" error?
- ✓ Ensure `.env` file exists in project root
- ✓ Verify variable names match exactly: `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`
- ✓ Restart Django development server

### Images served locally instead of from Cloudinary?
- ✓ Ensure `DEFAULT_FILE_STORAGE` is set to `cloudinary_storage.storage.MediaCloudinaryStorage`
- ✓ Run migrations if you just updated models

## Additional Resources

- [Cloudinary Django Docs](https://cloudinary.com/documentation/django_integration)
- [Cloudinary Dashboard](https://cloudinary.com/console)
- [Image Transformation Guide](https://cloudinary.com/documentation/image_transformation_reference)

## Next Steps

1. Copy your Cloudinary credentials to `.env`
2. Run `python manage.py migrate`
3. Test by uploading an image through the API or admin panel
4. Monitor your Cloudinary dashboard for successful uploads
