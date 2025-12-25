# Database Optimization & Realtime Plan

## Optimization Philosophy
No cache - realtime queries only. Use proper indexes, covering indexes, and database-level optimizations.

---

## Hot Path Analysis

### 1. Assignment Lookups (Most Critical - every visitor request)
```sql
-- Current query in assignment_repository.get_assignment()
SELECT * FROM assignments 
WHERE experiment_id = $1 AND user_id = $2
```
**Existing Index:** `idx_assignments_lookup` ✅
**Status:** Already optimized with composite index

### 2. Variant Stats by Experiment (Analytics - high frequency)
```sql
-- Current query in variant_repository.get_variants_for_experiment()
SELECT ev.*, ee.id FROM element_variants ev
JOIN experiment_elements ee ON ev.element_id = ee.id
WHERE ee.experiment_id = $1
```
**Current:** Requires JOIN, no covering index
**Optimization:** Add covering index on experiment_elements

### 3. Conversion Timeline (Dashboard - medium frequency)
```sql
-- Current query in assignment_repository.get_conversion_timeline()
SELECT DATE_TRUNC('hour', assigned_at), COUNT(*), COUNT(converted_at)
FROM assignments
WHERE experiment_id = $1 AND assigned_at >= NOW() - INTERVAL '1 hour' * $2
GROUP BY DATE_TRUNC('hour', assigned_at)
```
**Current:** Uses btree index on assigned_at
**Optimization:** BRIN index for time-series data

---

## Proposed Index Optimizations

### Migration: Performance Indexes

```sql
-- 1. Covering index for variant lookups (avoids JOIN)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_elements_experiment_covering
ON experiment_elements (experiment_id) INCLUDE (id, name, selector);

-- 2. Covering index for variant stats
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_variants_element_covering  
ON element_variants (element_id) INCLUDE (total_allocations, total_conversions, conversion_rate);

-- 3. BRIN index for time-series analytics (huge savings for large tables)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assignments_assigned_at_brin
ON assignments USING BRIN (assigned_at);

-- 4. Partial index for active experiments only
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_experiments_active
ON experiments (user_id, created_at DESC) 
WHERE status = 'active';

-- 5. Partial index for unconverted assignments (conversion tracking)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_assignments_unconverted
ON assignments (experiment_id, assigned_at DESC)
WHERE converted_at IS NULL;

-- 6. Composite for leads queue
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_leads_status_created
ON leads (status, created_at DESC);
```

---

## Query Pattern Optimizations

### 1. Use SELECT with specific columns (no SELECT *)
**Problem:** `SELECT *` fetches all columns including large JSONB payloads
**Solution:** Only select needed columns

### 2. Prepared Statements for Hot Paths  
**Problem:** Query planning overhead on each request
**Solution:** Use asyncpg's prepared statements for repeated queries

### 3. Connection Pool Tuning
**Current:** Default pool settings
**Optimization:** 
```python
pool = await asyncpg.create_pool(
    min_size=5,
    max_size=20,
    command_timeout=10,
    statement_cache_size=1024  # Cache prepared statements
)
```

### 4. Batch Operations
**Problem:** Multiple individual INSERTs
**Solution:** Use `executemany` or `COPY` for bulk operations

---

## Supabase Realtime Configuration

Enable Postgres changes for realtime without application-level caching:

```sql
-- Enable realtime for critical tables
ALTER PUBLICATION supabase_realtime ADD TABLE assignments;
ALTER PUBLICATION supabase_realtime ADD TABLE element_variants;
ALTER PUBLICATION supabase_realtime ADD TABLE conversions;
```

---

## Implementation Priority

| Priority | Optimization | Expected Impact |
|----------|-------------|----------------|
| 🔥 HIGH | Covering indexes for variants | 50-70% faster variant lookups |
| 🔥 HIGH | BRIN index for time-series | 90% faster analytics queries |
| ⚡ MED | Partial index for active experiments | 40-60% faster experiment list |
| ⚡ MED | Prepared statements | 10-20% reduction in latency |
| 💡 LOW | Connection pool tuning | 5-10% overall improvement |
