# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python app.py
# App runs on http://localhost:5000

# Test with two browser windows
# Open http://localhost:5000 in two separate windows to test matching
```

### Production Deployment (Render)
```bash
# Deploy to Render (automatic on git push)
git push origin main

# Access admin panel
# https://anonymous-chat-4ny5.onrender.com/admin?password=admin123
```

### Database Operations
```bash
# Database tables are auto-created on first run via db.create_all() in wsgi.py
# No manual migration needed for schema changes - just restart the app

# To reset local database
rm chat.db
python app.py  # Tables will be recreated
```

## Architecture Overview

This is a real-time anonymous chat application using Flask + Socket.IO with three matching modes:

### Core Components

**1. Matching System (matching_queue.py)**
- `MatchingQueue` class manages two separate queues:
  - `queue`: Random matching (FIFO deque)
  - `keyword_queue`: Keyword-based matching (dict: keyword -> [user_ids])
  - `user_profiles`: Stores user profiles for keyword matching
- All queue operations are thread-safe with `threading.Lock`
- **Critical**: Users must be added to queue BEFORE calling try_match/try_keyword_match
- Random matching: First-in-first-out between two users
- Keyword matching: Uses Jaccard similarity coefficient (intersection/union)

**2. Keyword Matching (keyword_matcher.py)**
- `KeywordMatcher.extract_keywords()`: Extracts keywords from text using:
  - Removes special characters, splits on spaces/punctuation
  - Filters stop words (defined in STOP_WORDS set)
  - Returns top keywords by frequency
- `KeywordMatcher.calculate_similarity()`: Jaccard similarity between keyword sets

**3. Room Keys (room_key_generator.py)**
- Generates 8-character keys using safe charset (avoids 0OI1l)
- `generate_unique_key()`: Ensures no collisions with existing keys
- Keys are stored in `ChatRoom.room_key` database field

**4. Socket.IO Events (app.py)**

**Client → Server:**
- `join_queue` - Random matching (no profile)
- `join_queue_with_profile` - Keyword matching with profile data
  - **Important**: Must call `matching_queue.add_with_profile()` BEFORE `try_keyword_match()`
  - If no match found, user stays in keyword queue waiting for others
- `create_private_room` - Creates private room with unique key
- `join_private_room` - Join existing room via key
- `send_message` - Send chat message
- `leave_room_event` - Leave current room

**Server → Client:**
- `waiting` - User is in queue waiting
- `matched` - Random match successful
- `matched_with_score` - Keyword match successful (includes similarity score)
- `private_room_created` - Private room created (includes room_key)
- `joined_private_room` - Successfully joined private room (includes has_history flag)
- `room_history` - Historical messages loaded
- `new_message` - New message received
- `partner_left` - Other user left
- `error` - Error message

### State Management

**Online Users (`online_users` dict):**
```python
{user_id: {'sid': socketio_session_id, 'room_id': room_id_or_none}}
```
- Tracks all connected users
- Updated on: connect, match, leave, disconnect
- Used for routing messages to specific users

**Application States (chat.js):**
- `INIT` - Start screen (three buttons: random match, private room, join by key)
- `WAITING` - Waiting screen with spinner
- `CHATTING` - Active chat interface

**Match Types:**
- `random` - Traditional random matching
- `keyword` - Matching based on keyword similarity
- `private` - Private room with shared key

### Database Models (models.py)

**ChatRoom:**
- `user1_id`, `user2_id` - Two users in room (user2_id nullable for private rooms)
- `room_key` - Unique 8-char key (only for private rooms)
- `match_type` - 'random', 'keyword', or 'private'
- `is_private` - Boolean flag
- `is_active` - Room status
- `messages` - Relationship to Message records

**Message:**
- `room_id` - Foreign key to ChatRoom
- `sender_id` - Which user sent it
- `content` - Message text (max 500 chars)
- `timestamp` - Beijing time (UTC+8)

**UserProfile:**
- `user_id` - Unique identifier
- `bio`, `purpose` - User-provided text
- `keywords` - JSON array of extracted keywords

### Time Handling
- All timestamps use Beijing time (UTC+8) via `get_beijing_time()` in models.py
- Stored in UTC+8 in database
- Displayed with `toLocaleTimeString('zh-CN')` in frontend

### Critical Configuration Details

**eventlet Compatibility (config.py):**
```python
SQLALCHEMY_ENGINE_OPTIONS = {
    'poolclass': NullPool,  # Required for eventlet compatibility
    'pool_pre_ping': True
}
```
- **Must use NullPool** - SQLAlchemy's default QueuePool is incompatible with eventlet green threads
- Causes "cannot notify on un-acquired lock" errors if misconfigured
- eventlet 0.37.0+ required for Python 3.13 compatibility

**Session Management:**
- Flask-Session with filesystem storage
- User IDs stored in session, persist across socket.io connections
- Session ID maps to Socket.IO session ID in `online_users`

### Frontend State Machine (chat.js)

**Screen Switching:**
- `switchScreen(state)` - Removes all 'active' classes, adds to target screen
- Forms use `.hidden` class instead (CSS: `display: none !important`)
- Three main screens: start-screen, waiting-screen, chat-screen
- Two forms: profile-form, join-room-form

**Key Variables:**
- `currentRoomId` - Current chat room ID
- `currentRoomKey` - Room key (null unless private room)
- `currentMatchType` - 'random', 'keyword', or 'private'

### Common Pitfalls

**1. Keyword Matching Queue Logic:**
```python
# WRONG - User never gets added to queue
match_result = matching_queue.try_keyword_match(user_id, profile)

# RIGHT - Add first, then try matching
matching_queue.add_with_profile(user_id, profile)
match_result = matching_queue.try_keyword_match(user_id, profile)
```

**2. Form State Management:**
```javascript
// WRONG - Keeps form visible
profileForm.classList.add('active');

// RIGHT - Hide form before switching
profileForm.classList.remove('active');
switchScreen(AppState.WAITING);
```

**3. Database URL Format:**
- Render provides `postgres://` URL
- Must be replaced with `postgresql://` for SQLAlchemy
- Handled automatically in config.py

**4. Message Routing:**
- Use `socketio.emit(..., room=room_id)` to broadcast to both users
- Use `emit(...)` to send only to current user
- `join_room()` and `leave_room()` manage Socket.IO room membership

### Testing Multiple Users

**Local Testing:**
1. Open browser in incognito window (user 1)
2. Open another browser or regular window (user 2)
3. Both will get different UUIDs from Flask session

**Production Testing:**
- Use two different devices (phone + computer)
- Or two browsers with different cookies
- Direct URL: https://anonymous-chat-4ny5.onrender.com

### Admin Panel
- Route: `/admin?password=<ADMIN_PASSWORD>`
- Default password: `admin123` (set via ADMIN_PASSWORD env var)
- Features: View all rooms/messages, export CSV (Excel-compatible), export JSON
- Uses UTF-8 BOM for CSV Excel compatibility

### Environment Variables
- `SECRET_KEY` - Flask session encryption (required in production)
- `DATABASE_URL` - PostgreSQL connection string (required for persistence)
- `ADMIN_PASSWORD` - Admin panel access (default: admin123)
- `WEB_CONCURRENCY` - Worker count (keep at 1 for memory queue sharing)
