# public_api/routers/blog.py

"""
Blog Router - Markdown-based content system
Reads .md files from content/blog/ and renders them as HTML
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import HTMLResponse
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import frontmatter
import markdown
import logging
import time

from public_api.models import APIResponse, PaginatedResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

# ════════════════════════════════════════════════════════════════════════════
# MODELS
# ════════════════════════════════════════════════════════════════════════════

class BlogPostMetadata(BaseModel):
    title: str
    slug: str
    category: str
    author: str = "Samplit Team"
    date: datetime
    excerpt: str
    keywords: List[str]
    image: Optional[str] = None
    published: bool = True
    reading_time: Optional[int] = None

class BlogPostResponse(BaseModel):
    metadata: BlogPostMetadata
    content: str  # HTML
    html_content: str  # Alias for compatibility

class BlogListItem(BaseModel):
    title: str
    slug: str
    category: str
    excerpt: str
    date: datetime
    image: Optional[str] = None
    reading_time: Optional[int] = None

# ════════════════════════════════════════════════════════════════════════════
# CACHE
# ════════════════════════════════════════════════════════════════════════════

blog_cache: Dict[str, tuple[float, Any]] = {}
CACHE_TTL = 3600  # 1 hour

def get_cached(key: str) -> Optional[Any]:
    if key in blog_cache:
        cached_at, content = blog_cache[key]
        if time.time() - cached_at < CACHE_TTL:
            return content
    return None

def set_cached(key: str, content: Any):
    blog_cache[key] = (time.time(), content)

# ════════════════════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════════════════════

BLOG_DIR = Path(__file__).parent.parent.parent / "content" / "blog"

def calculate_reading_time(content: str) -> int:
    """Estimate reading time in minutes (200 words/min)"""
    words = len(content.split())
    return max(1, round(words / 200))

def parse_markdown_file(filepath: Path) -> Optional[Dict[str, Any]]:
    """Parse markdown file with frontmatter"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)
            
        # Validate required fields
        required = ['title', 'slug', 'category', 'date', 'excerpt']
        for field in required:
            if field not in post.metadata:
                logger.warning(f"Missing required field '{field}' in {filepath}")
                return None
        
        # Convert markdown to HTML
        md = markdown.Markdown(extensions=[
            'fenced_code',
            'tables',
            'toc',
            'codehilite',
            'nl2br'
        ])
        html_content = md.convert(post.content)
        
        # Calculate reading time if not provided
        reading_time = post.metadata.get('reading_time') or calculate_reading_time(post.content)
        
        return {
            'metadata': {
                **post.metadata,
                'reading_time': reading_time,
                'date': post.metadata['date'] if isinstance(post.metadata['date'], datetime) else datetime.fromisoformat(str(post.metadata['date']))
            },
            'content': html_content
        }
    except Exception as e:
        logger.error(f"Error parsing {filepath}: {e}")
        return None

def get_all_posts() -> List[Dict[str, Any]]:
    """Get all published blog posts"""
    cached = get_cached('all_posts')
    if cached:
        return cached
    
    posts = []
    
    # Scan all subdirectories
    for category_dir in BLOG_DIR.iterdir():
        if not category_dir.is_dir() or category_dir.name.startswith('.'):
            continue
            
        for md_file in category_dir.glob('*.md'):
            if md_file.name == 'README.md':
                continue
                
            post_data = parse_markdown_file(md_file)
            if post_data and post_data['metadata'].get('published', True):
                posts.append(post_data)
    
    # Sort by date (newest first)
    posts.sort(key=lambda x: x['metadata']['date'], reverse=True)
    
    set_cached('all_posts', posts)
    return posts

def get_post_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    """Get single post by slug"""
    cached = get_cached(f'post_{slug}')
    if cached:
        return cached
    
    # Search all categories
    for category_dir in BLOG_DIR.iterdir():
        if not category_dir.is_dir():
            continue
            
        for md_file in category_dir.glob('*.md'):
            post_data = parse_markdown_file(md_file)
            if post_data and post_data['metadata'].get('slug') == slug:
                set_cached(f'post_{slug}', post_data)
                return post_data
    
    return None

# ════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════

@router.get("/", response_model=PaginatedResponse[BlogListItem])
async def list_blog_posts(
    category: Optional[str] = Query(None, description="Filter by category"),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50)
):
    """List all blog posts with pagination"""
    try:
        all_posts = get_all_posts()
        
        # Filter by category if specified
        if category:
            all_posts = [p for p in all_posts if p['metadata']['category'] == category]
        
        # Pagination
        total = len(all_posts)
        start = (page - 1) * per_page
        end = start + per_page
        posts_page = all_posts[start:end]
        
        # Convert to list items
        items = [
            BlogListItem(
                title=p['metadata']['title'],
                slug=p['metadata']['slug'],
                category=p['metadata']['category'],
                excerpt=p['metadata']['excerpt'],
                date=p['metadata']['date'],
                image=p['metadata'].get('image'),
                reading_time=p['metadata'].get('reading_time')
            )
            for p in posts_page
        ]
        
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        logger.error(f"Error listing blog posts: {e}")
        raise HTTPException(status_code=500, detail="Failed to load blog posts")

@router.get("/{slug}", response_model=BlogPostResponse)
async def get_blog_post(slug: str):
    """Get single blog post by slug"""
    try:
        post_data = get_post_by_slug(slug)
        
        if not post_data:
            raise HTTPException(status_code=404, detail="Blog post not found")
        
        return BlogPostResponse(
            metadata=BlogPostMetadata(**post_data['metadata']),
            content=post_data['content'],
            html_content=post_data['content']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading blog post {slug}: {e}")
        raise HTTPException(status_code=500, detail="Failed to load blog post")

@router.get("/category/{category}", response_model=List[BlogListItem])
async def get_posts_by_category(category: str):
    """Get all posts in a specific category"""
    try:
        all_posts = get_all_posts()
        category_posts = [p for p in all_posts if p['metadata']['category'] == category]
        
        return [
            BlogListItem(
                title=p['metadata']['title'],
                slug=p['metadata']['slug'],
                category=p['metadata']['category'],
                excerpt=p['metadata']['excerpt'],
                date=p['metadata']['date'],
                image=p['metadata'].get('image'),
                reading_time=p['metadata'].get('reading_time')
            )
            for p in category_posts
        ]
        
    except Exception as e:
        logger.error(f"Error loading category {category}: {e}")
        raise HTTPException(status_code=500, detail="Failed to load category posts")

@router.post("/cache/clear", response_model=APIResponse)
async def clear_blog_cache():
    """Clear blog cache (admin only in production)"""
    global blog_cache
    blog_cache = {}
    return APIResponse(success=True, message="Blog cache cleared")
