# 🎧 Audiobook Platform - Database Design Document

## 🧩 Overview
This document presents the **database schema** for an audiobook streaming platform that enables users to **discover, listen to, and track their progress** across a catalog of audiobooks.

The design prioritizes:
- **Data integrity**
- **Query performance**
- **Scalability**

It supports core features such as:
- User authentication
- Audiobook discovery
- Listening progress tracking
- Reviews and ratings
- Personalized recommendations

---

## 🗃️ Entities

### 👤 User
Represents registered users of the platform.

- Extends Django’s `AbstractUser` to leverage built-in authentication.
- Adds platform-specific fields like:
  - `profile_avatar`
  - `bio`
- `email` is **unique** to serve as an alternative login identifier.
- `created_at` and `updated_at` enable auditing and analytics around user growth.

---

### 🎵 Entity (Audiobook)
Represents the core content of the platform.

- `audio_file` stores a **URL reference to AWS S3**, not binary data in PostgreSQL.
- `title` is **indexed** for efficient search queries.
- Cached aggregation fields include:
  - `average_rating`
  - `total_ratings`
  - `total_reviews`
  - `play_count`

These are updated incrementally through **database triggers** or **Django signals**.

**Publisher** is stored as a simple `CharField`, since publishers don’t need their own profiles at this stage.

---

### ✍️ Author
- Avoids data duplication by separating from Audiobook.
- Supports **many-to-many** relationships for co-authored works.
- Fields:
  - `bio`
  - `photo`
  - `links` (`JSONField`) for multiple URLs or social profiles.

---

### 🎙️ Narrator
- Separate from Author — narrators and authors are distinct roles.
- Supports **many-to-many** relationships with audiobooks.
- Mirrors Author’s structure for consistency.

---

### 🏷️ Genre
- Enables categorization and filtering.
- Simple structure: `name`, `description`.
- **Many-to-many** relationship with Audiobooks for multi-genre classification (e.g. *Science Fiction + Thriller*).

---

### 🎧 ListeningProgress
Tracks playback state for each **user–audiobook pair**.

- `UNIQUE` constraint on `(user, audiobook)` ensures one record per pair.
- Key fields:
  - `current_position`: for resume playback
  - `is_favorite`: merged from Library table for simplicity
  - `is_completed`: tracks explicit completion
  - `last_listened_at`: enables sorting by activity for “Continue Listening”

---

### ⭐ Review
Enables user-generated ratings and reviews.

- `UNIQUE (user, audiobook)` → one review per user per book.
- `rating` field has a `CHECK` constraint (1–5).
- `helpful_count` tracks community feedback (like “Was this review helpful?”).

---

## 🔗 Relationships

| Relationship | Type | Description |
|---------------|------|--------------|
| **User ↔ Audiobook (via ListeningProgress)** | Many-to-Many | Tracks position, completion, favorites |
| **User ↔ Audiobook (via Review)** | Many-to-Many | Holds user ratings and reviews |
| **Audiobook ↔ Author** | Many-to-Many | Supports co-authored books |
| **Audiobook ↔ Narrator** | Many-to-Many | Handles multiple narrators per audiobook |
| **Audiobook ↔ Genre** | Many-to-Many | Enables multi-genre classification |

---

## ⚙️ Key Design Decisions

### 1. Merged User Library into ListeningProgress
**Rationale:**
- Reduces schema complexity (one table instead of two)
- Simplifies queries (favorites come from ListeningProgress)
- Matches real-world usage (favorites usually imply progress)

If more collection features are needed later, they can be added separately.

---

### 2. Cached Aggregation Fields on Audiobook
**Rationale:**
- Improves performance — no need to recompute aggregates each time.
- Scales better for large datasets.
- Updated via Django signals on relevant events (new review, completed session).

**Trade-off:** Slight chance of temporary inconsistency during concurrent writes, acceptable for non-critical metrics.

---

### 3. Audio Files Stored Outside Database
**Rationale:**
- Databases are optimized for structured data, not large binary files.
- AWS S3 + CDN ensures global scalability and performance.
- Cheaper and easier to manage.
- Flexible for multiple audio qualities or downloads.

---

### 4. Publisher as CharField
**Rationale:**
- Publishers don’t need detailed profiles at this stage.
- Avoids premature optimization.
- Can be refactored into a separate entity later.

---

### 5. No Separate Chapter Entity
**Rationale:**
- Time constraint: 3-week timeline.
- Chapters add complexity (extra endpoints, UI, and data).
- Non-essential for MVP functionality.
- Future-proof: Can be added later without schema disruption.

---

## ⚡ Performance Optimizations

### 🧱 Database Indexes
| Field | Purpose |
|--------|----------|
| `Entity.title` | Fast search and autocomplete |
| `Author.name` | Filter and search by author |
| `Genre.name` | Genre-based filtering |
| `ListeningProgress.last_listened_at` | Sort by recent activity |
| `Review.created_at` | Display recent reviews |

---

### 🚀 Query Optimization
- Use `select_related()` for foreign key joins.
- Use `prefetch_related()` for many-to-many relationships.
- Implement **pagination** on list endpoints.
- Cache frequently accessed data (genres, top-rated audiobooks).

---

## 🧩 Data Integrity
- **UNIQUE constraints** prevent duplicate records.
- **CHECK constraints** enforce rating validity (1–5).
- **CASCADE DELETE** ensures related data cleanup.
- **Required fields** ensure completeness of essential data.

---

## 🌱 Future Scalability

This schema is designed to evolve easily:

| Feature | Extension |
|----------|------------|
| Chapter Navigation | Add `Chapter` entity with FK to Audiobook |
| User Collections | Add `UserCollection` and `CollectionItem` tables |
| Social Features | Add `UserFollow` and `ActivityFeed` |
| Recommendations | Support collaborative filtering using listening and rating history |
| Moderation | Add `moderation_status` and `moderation_notes` fields if user uploads are introduced |

---

## ✅ Conclusion
The **normalized design** and **clear separation of concerns** make this schema robust, scalable, and adaptable for future product evolution — enabling a rich audiobook experience built on solid data foundations.
