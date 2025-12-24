# How to Connect to MongoDB Atlas and Check Data

## Quick Method (Using Python Script)

I've created scripts in `backend/scripts/` that connect to your Atlas database:

### 1. Check Blog Post Fields
```bash
cd G:\Desktop\visionai\backend\scripts
python check_blog_data.py
```

This shows all fields in your blog posts and identifies missing ones.

### 2. Check Database Contents
```bash
python check_atlas_db.py
```

Shows all collections and document counts.

---

## Connection Details

Your MongoDB Atlas connection:
- **Cluster**: `synovae.wvyba4e.mongodb.net`
- **Database**: `synovae_db`
- **Collection**: `blog_posts`

---

## What I Found

**Missing Field**: `excerpt`

The blog posts have these fields:
- ✅ title
- ✅ slug  
- ✅ featured_image
- ✅ published_at
- ✅ reading_time
- ✅ author (with name)
- ✅ categories
- ✅ tags
- ✅ views
- ❌ **excerpt** (MISSING - causes errors)

---

## Fix Applied

Running `fix_blog_excerpts.py` to automatically generate excerpts from the blog content for all 3 posts.
