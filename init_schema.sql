-- ============================================================================
-- FastAPI Base 数据库初始化 SQL
-- 适用于 SQLite 数据库
-- 生成时间: 2025-11-28
-- ============================================================================

-- 用户表
CREATE TABLE IF NOT EXISTS "users" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "username" VARCHAR(50) NOT NULL UNIQUE,
    "email" VARCHAR(100) NOT NULL UNIQUE,
    "hashed_password" VARCHAR(255) NOT NULL,
    "is_active" INTEGER NOT NULL DEFAULT 1,
    "is_superuser" INTEGER NOT NULL DEFAULT 0,
    "is_staff" INTEGER NOT NULL DEFAULT 0,
    "last_login" TIMESTAMP NULL,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 用户资料表
CREATE TABLE IF NOT EXISTS "user_profiles" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "user_id" INTEGER NOT NULL UNIQUE,
    "first_name" VARCHAR(50) NULL,
    "last_name" VARCHAR(50) NULL,
    "phone" VARCHAR(20) NULL,
    "avatar" VARCHAR(255) NULL,
    "bio" TEXT NULL,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "fk_user_profiles_user" FOREIGN KEY ("user_id") REFERENCES "users" ("id") ON DELETE CASCADE
);

-- ============================================================================
-- Celery Beat 定时任务表 (类似 django-celery-beat)
-- ============================================================================

-- 间隔调度表
CREATE TABLE IF NOT EXISTS "celery_interval_schedule" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "every" INTEGER NOT NULL,
    "period" VARCHAR(24) NOT NULL,
    UNIQUE ("every", "period")
);

-- Crontab 调度表
CREATE TABLE IF NOT EXISTS "celery_crontab_schedule" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "minute" VARCHAR(240) NOT NULL DEFAULT '*',
    "hour" VARCHAR(96) NOT NULL DEFAULT '*',
    "day_of_week" VARCHAR(64) NOT NULL DEFAULT '*',
    "day_of_month" VARCHAR(124) NOT NULL DEFAULT '*',
    "month_of_year" VARCHAR(64) NOT NULL DEFAULT '*',
    "timezone" VARCHAR(64) NOT NULL DEFAULT 'Asia/Shanghai'
);

-- 定时任务表
CREATE TABLE IF NOT EXISTS "celery_periodic_task" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "name" VARCHAR(200) NOT NULL UNIQUE,
    "task" VARCHAR(200) NOT NULL,
    "interval_id" INTEGER NULL,
    "crontab_id" INTEGER NULL,
    "args" TEXT NOT NULL DEFAULT '[]',
    "kwargs" TEXT NOT NULL DEFAULT '{}',
    "queue" VARCHAR(200) NULL,
    "exchange" VARCHAR(200) NULL,
    "routing_key" VARCHAR(200) NULL,
    "priority" INTEGER NULL,
    "expires" TIMESTAMP NULL,
    "expire_seconds" INTEGER NULL,
    "one_off" INTEGER NOT NULL DEFAULT 0,
    "start_time" TIMESTAMP NULL,
    "enabled" INTEGER NOT NULL DEFAULT 1,
    "last_run_at" TIMESTAMP NULL,
    "total_run_count" INTEGER NOT NULL DEFAULT 0,
    "date_changed" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "description" TEXT NULL,
    "created_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "fk_periodic_task_interval" FOREIGN KEY ("interval_id") REFERENCES "celery_interval_schedule" ("id") ON DELETE SET NULL,
    CONSTRAINT "fk_periodic_task_crontab" FOREIGN KEY ("crontab_id") REFERENCES "celery_crontab_schedule" ("id") ON DELETE SET NULL
);

-- 定时任务变更标记表
CREATE TABLE IF NOT EXISTS "celery_periodic_task_changed" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "last_update" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 任务执行结果表
CREATE TABLE IF NOT EXISTS "celery_task_result" (
    "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    "task_id" VARCHAR(255) NOT NULL UNIQUE,
    "task_name" VARCHAR(255) NULL,
    "task_args" TEXT NULL,
    "task_kwargs" TEXT NULL,
    "status" VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    "result" TEXT NULL,
    "traceback" TEXT NULL,
    "date_created" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "date_done" TIMESTAMP NULL,
    "worker" VARCHAR(100) NULL
);

-- ============================================================================
-- 索引
-- ============================================================================

-- 用户表索引
CREATE INDEX IF NOT EXISTS "idx_users_username" ON "users" ("username");
CREATE INDEX IF NOT EXISTS "idx_users_email" ON "users" ("email");
CREATE INDEX IF NOT EXISTS "idx_users_is_active" ON "users" ("is_active");

-- 定时任务表索引
CREATE INDEX IF NOT EXISTS "idx_periodic_task_enabled" ON "celery_periodic_task" ("enabled");
CREATE INDEX IF NOT EXISTS "idx_periodic_task_name" ON "celery_periodic_task" ("name");

-- 任务结果表索引
CREATE INDEX IF NOT EXISTS "idx_task_result_task_id" ON "celery_task_result" ("task_id");
CREATE INDEX IF NOT EXISTS "idx_task_result_task_name" ON "celery_task_result" ("task_name");
CREATE INDEX IF NOT EXISTS "idx_task_result_status" ON "celery_task_result" ("status");
CREATE INDEX IF NOT EXISTS "idx_task_result_date_created" ON "celery_task_result" ("date_created");

-- ============================================================================
-- 初始数据
-- ============================================================================

-- 初始化定时任务变更标记
INSERT OR IGNORE INTO "celery_periodic_task_changed" ("id", "last_update") VALUES (1, CURRENT_TIMESTAMP);

-- 创建默认间隔调度
INSERT OR IGNORE INTO "celery_interval_schedule" ("id", "every", "period") VALUES (1, 10, 'seconds');
INSERT OR IGNORE INTO "celery_interval_schedule" ("id", "every", "period") VALUES (2, 1, 'minutes');
INSERT OR IGNORE INTO "celery_interval_schedule" ("id", "every", "period") VALUES (3, 5, 'minutes');
INSERT OR IGNORE INTO "celery_interval_schedule" ("id", "every", "period") VALUES (4, 10, 'minutes');
INSERT OR IGNORE INTO "celery_interval_schedule" ("id", "every", "period") VALUES (5, 30, 'minutes');
INSERT OR IGNORE INTO "celery_interval_schedule" ("id", "every", "period") VALUES (6, 1, 'hours');
INSERT OR IGNORE INTO "celery_interval_schedule" ("id", "every", "period") VALUES (7, 1, 'days');

-- 创建默认 Crontab 调度
-- 每天凌晨执行
INSERT OR IGNORE INTO "celery_crontab_schedule" ("id", "minute", "hour", "day_of_week", "day_of_month", "month_of_year", "timezone") 
VALUES (1, '0', '0', '*', '*', '*', 'Asia/Shanghai');
-- 每小时执行
INSERT OR IGNORE INTO "celery_crontab_schedule" ("id", "minute", "hour", "day_of_week", "day_of_month", "month_of_year", "timezone") 
VALUES (2, '0', '*', '*', '*', '*', 'Asia/Shanghai');
-- 每周一凌晨执行
INSERT OR IGNORE INTO "celery_crontab_schedule" ("id", "minute", "hour", "day_of_week", "day_of_month", "month_of_year", "timezone") 
VALUES (3, '0', '0', '1', '*', '*', 'Asia/Shanghai');

-- 创建示例定时任务 - Hello World 每10秒执行
INSERT OR IGNORE INTO "celery_periodic_task" (
    "id", "name", "task", "interval_id", "args", "kwargs", "enabled", "description"
) VALUES (
    1, 
    'hello-world-task', 
    'celery_app.tasks.test_tasks.hello_world',
    1,
    '[]',
    '{}',
    1,
    '测试任务 - 每10秒打印 Hello World'
);

-- ============================================================================
-- 触发器 (用于自动更新 updated_at 字段)
-- ============================================================================

-- 用户表更新触发器
CREATE TRIGGER IF NOT EXISTS "update_users_timestamp" 
AFTER UPDATE ON "users"
FOR EACH ROW
BEGIN
    UPDATE "users" SET "updated_at" = CURRENT_TIMESTAMP WHERE "id" = OLD."id";
END;

-- 用户资料表更新触发器
CREATE TRIGGER IF NOT EXISTS "update_user_profiles_timestamp" 
AFTER UPDATE ON "user_profiles"
FOR EACH ROW
BEGIN
    UPDATE "user_profiles" SET "updated_at" = CURRENT_TIMESTAMP WHERE "id" = OLD."id";
END;

-- 定时任务表更新触发器
CREATE TRIGGER IF NOT EXISTS "update_periodic_task_timestamp" 
AFTER UPDATE ON "celery_periodic_task"
FOR EACH ROW
BEGIN
    UPDATE "celery_periodic_task" SET "updated_at" = CURRENT_TIMESTAMP WHERE "id" = OLD."id";
END;

-- 定时任务变更通知触发器 (当定时任务表有变化时，更新变更标记)
CREATE TRIGGER IF NOT EXISTS "notify_periodic_task_changed_insert" 
AFTER INSERT ON "celery_periodic_task"
BEGIN
    UPDATE "celery_periodic_task_changed" SET "last_update" = CURRENT_TIMESTAMP WHERE "id" = 1;
END;

CREATE TRIGGER IF NOT EXISTS "notify_periodic_task_changed_update" 
AFTER UPDATE ON "celery_periodic_task"
BEGIN
    UPDATE "celery_periodic_task_changed" SET "last_update" = CURRENT_TIMESTAMP WHERE "id" = 1;
END;

CREATE TRIGGER IF NOT EXISTS "notify_periodic_task_changed_delete" 
AFTER DELETE ON "celery_periodic_task"
BEGIN
    UPDATE "celery_periodic_task_changed" SET "last_update" = CURRENT_TIMESTAMP WHERE "id" = 1;
END;

-- ============================================================================
-- 完成
-- ============================================================================
-- 使用方法:
-- sqlite3 default_db.sqlite3 < init_schema.sql
-- 
-- 或者在 Python 中:
-- import sqlite3
-- conn = sqlite3.connect('default_db.sqlite3')
-- with open('init_schema.sql', 'r') as f:
--     conn.executescript(f.read())
-- conn.close()
-- ============================================================================
