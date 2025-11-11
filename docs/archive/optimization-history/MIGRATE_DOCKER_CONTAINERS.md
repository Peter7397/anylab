# 🔄 Docker Container Migration Guide

## Current Situation

Your Docker containers are still named with the old "onlab" prefix:
- `onlab_postgres` (PostgreSQL)
- `onlab_redis` (Redis)

But the code has been updated to use:
- `anylab_postgres` (PostgreSQL)
- `anylab_redis` (Redis)

## Migration Options

### Option 1: Stop and Remove Old Containers (Recommended)

This is the cleanest approach. Your data is safe because it's stored in Docker volumes.

**Steps:**

1. **Stop the old containers:**
   ```bash
   docker stop onlab_postgres onlab_redis
   ```

2. **Remove the old containers:**
   ```bash
   docker rm onlab_postgres onlab_redis
   ```

3. **Start new containers with correct names:**
   ```bash
   ./start-docker-services.sh
   ```
   OR
   ```bash
   docker-compose up -d postgres redis
   ```

**Data Safety:** Your PostgreSQL data is stored in the `postgres_data` volume, so it will persist. The new container will use the same volume.

### Option 2: Rename Existing Containers (Alternative)

If you want to keep the containers running without downtime:

1. **Stop the containers:**
   ```bash
   docker stop onlab_postgres onlab_redis
   ```

2. **Rename them:**
   ```bash
   docker rename onlab_postgres anylab_postgres
   docker rename onlab_redis anylab_redis
   ```

3. **Start them again:**
   ```bash
   docker start anylab_postgres anylab_redis
   ```

### Option 3: Use Both Names Temporarily (Safest)

Keep both sets of containers running temporarily, then migrate:

1. **Start new containers (they'll use different ports or volumes):**
   ```bash
   docker-compose up -d postgres redis
   ```

2. **Verify new containers work:**
   ```bash
   docker ps | grep anylab
   ```

3. **Stop and remove old containers once verified:**
   ```bash
   docker stop onlab_postgres onlab_redis
   docker rm onlab_postgres onlab_redis
   ```

## Verification Steps

After migration, verify everything works:

1. **Check containers are running:**
   ```bash
   docker ps | grep anylab
   ```

2. **Test PostgreSQL connection:**
   ```bash
   docker exec anylab_postgres pg_isready -U postgres
   ```

3. **Test Redis connection:**
   ```bash
   docker exec anylab_redis redis-cli ping
   ```

4. **Check database data is intact:**
   ```bash
   docker exec anylab_postgres psql -U postgres -d anylab -c "SELECT COUNT(*) FROM ai_assistant_uploadedfile;"
   ```

## Important Notes

- **Data is safe:** Docker volumes persist data independently of container names
- **No data loss:** The `postgres_data` volume contains all your database data
- **Downtime:** Option 1 has minimal downtime (a few seconds)
- **Backup:** If you want extra safety, you can backup the volume first:
  ```bash
  docker run --rm -v anylab_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data
  ```

## Recommended Action

**I recommend Option 1** - it's clean, simple, and your data is safe in volumes.

Just run:
```bash
docker stop onlab_postgres onlab_redis
docker rm onlab_postgres onlab_redis
./start-docker-services.sh
```

This will create new containers with the correct names and use your existing data volumes.

