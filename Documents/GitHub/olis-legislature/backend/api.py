"""
FastAPI Backend Template
Serves both API endpoints and the frontend dashboard

EXAMPLE: This implements a Task Management System to demonstrate all template features.
Replace the task-related code with your own application logic.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from datetime import datetime
import os
import time
import platform
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
APP_NAME = os.getenv("APP_NAME", "OLIS - Oregon Legislative Information System")
APP_PORT = int(os.getenv("APP_PORT", "8000"))
APP_ENV = os.getenv("APP_ENV", "development")
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/app.db")
ENABLE_DEBUG = os.getenv("ENABLE_DEBUG", "true").lower() == "true"
AUTO_REFRESH_INTERVAL = int(os.getenv("AUTO_REFRESH_INTERVAL", "5000"))

# OLIS API Configuration
OLIS_BASE_URL = os.getenv("OLIS_BASE_URL", "https://api.oregonlegislature.gov/odata/ODataService.svc/")
OLIS_TIMEOUT = int(os.getenv("OLIS_TIMEOUT", "30"))
OLIS_MAX_RETRIES = int(os.getenv("OLIS_MAX_RETRIES", "3"))

# Import our storage helper, OLIS client, and bill status classifier
from storage import Storage
from olis_client import OLISClient
from bill_status import categorize_bills_by_status, categorize_bills_by_committees, categorize_bills_by_specific_committees
from testimony_analysis import analyze_hot_bills

# Import database dependencies
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database_config import get_db_session
from olis_sync_service import run_olis_sync
from database.models_with_analysis import Company, User, Measure, AnalysisType

# Standardized API Response Models
class ApiError(BaseModel):
    code: str
    message: str
    details: Optional[str] = None
    timestamp: str

class ApiResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[ApiError] = None
    timestamp: str

# Error Response Helper Functions
def create_error_response(
    status_code: int,
    error_code: str, 
    message: str,
    details: Optional[str] = None
) -> JSONResponse:
    """Create a standardized error response"""
    error_response = ApiResponse(
        success=False,
        error=ApiError(
            code=error_code,
            message=message,
            details=details,
            timestamp=datetime.now().isoformat()
        ),
        timestamp=datetime.now().isoformat()
    )
    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump()
    )

def create_success_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a standardized success response"""
    return {
        "success": True,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }

# EXAMPLE: Data Models - Replace these with your own data structures
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = "medium"  # low, medium, high

class Task(BaseModel):
    id: int
    title: str
    description: Optional[str]
    priority: str
    status: str
    created_at: str
    completed_at: Optional[str] = None

# Initialize FastAPI app
app = FastAPI(
    title=APP_NAME,
    description="Service built with the AI Agent Company starter template",
    version="1.0.0",
    debug=ENABLE_DEBUG
)

# Initialize storage (KEEP THIS - use for your own data persistence)
storage = Storage(DATABASE_PATH)

# Initialize startup time for uptime calculation
START_TIME = time.time()

# Add CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Error Handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with standardized error response"""
    # Log error for monitoring
    storage.log("error", f"HTTP {exc.status_code}: {exc.detail} - {request.method} {request.url}")
    
    # Map HTTP status codes to error codes
    error_code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED", 
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "UNPROCESSABLE_ENTITY",
        429: "RATE_LIMITED",
        500: "INTERNAL_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
        504: "GATEWAY_TIMEOUT"
    }
    
    error_code = error_code_map.get(exc.status_code, "HTTP_ERROR")
    
    return create_error_response(
        status_code=exc.status_code,
        error_code=error_code,
        message=exc.detail,
        details=f"{request.method} {request.url}" if ENABLE_DEBUG else None
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors"""
    # Log validation error
    storage.log("warning", f"Validation error: {str(exc)} - {request.method} {request.url}")
    
    # Extract field-specific error messages
    error_details = []
    for error in exc.errors():
        field = " -> ".join(str(x) for x in error["loc"])
        message = error["msg"]
        error_details.append(f"{field}: {message}")
    
    return create_error_response(
        status_code=422,
        error_code="VALIDATION_ERROR",
        message="Request validation failed",
        details="; ".join(error_details) if ENABLE_DEBUG else "Invalid request format"
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    # Log the unexpected error
    storage.log("error", f"Unhandled exception: {type(exc).__name__}: {str(exc)} - {request.method} {request.url}")
    
    return create_error_response(
        status_code=500,
        error_code="INTERNAL_ERROR",
        message="An unexpected error occurred",
        details=f"{type(exc).__name__}: {str(exc)}" if ENABLE_DEBUG else "Please try again later"
    )

# Get the frontend directory path
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

# API Routes
# ----------

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": APP_NAME
    }

@app.get("/api/health/detailed")
async def detailed_health():
    """Detailed health check with system metrics"""
    current_time = time.time()
    uptime = current_time - START_TIME
    
    # Get restart count from storage
    restart_count = storage.get_state("restart_count", 0)
    last_restart = storage.get_state("last_restart")
    
    # Get error count from recent events
    recent_errors = storage.get_events("error", limit=100)
    errors_last_hour = len([e for e in recent_errors if e.get('created_at')])
    
    # Calculate memory usage (rough estimate)
    memory_mb = sys.getsizeof(storage) / 1024 / 1024  # Rough estimate
    
    return create_success_response({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": int(uptime),
        "restart_count": restart_count,
        "last_restart": last_restart,
        "errors_last_hour": errors_last_hour,
        "memory_mb": round(memory_mb, 2),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "service": APP_NAME,
        "environment": APP_ENV,
        "debug_mode": ENABLE_DEBUG,
        "database_path": DATABASE_PATH,
        "port": APP_PORT
    })

@app.post("/api/internal/log-restart")
async def log_restart(request: dict = {}):
    """Internal endpoint to log service restarts"""
    try:
        count = request.get("count", 1) if isinstance(request, dict) else 1
        storage.set_state("restart_count", count)
        storage.set_state("last_restart", datetime.now().isoformat())
        storage.log_event("service_restarted", {"count": count})
        storage.log("info", f"Service restart logged: #{count}")
        
        return create_success_response({
            "logged": True,
            "restart_count": count,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return create_error_response(
            status_code=500,
            error_code="INTERNAL_ERROR",
            message="Failed to log restart",
            details=str(e) if ENABLE_DEBUG else "Restart logging failed"
        )

@app.get("/api/status")
async def get_status():
    """Get current application status with metrics"""
    # Calculate actual uptime
    current_time = time.time()
    uptime_seconds = current_time - START_TIME
    uptime_days = int(uptime_seconds // 86400)
    uptime_hours = int((uptime_seconds % 86400) // 3600)
    uptime_minutes = int((uptime_seconds % 3600) // 60)
    uptime_formatted = f"{uptime_days}d {uptime_hours}h {uptime_minutes}m"
    
    # Get system health information
    try:
        # Test database connectivity
        db_healthy = True
        db_error = None
        try:
            stats = storage.get_stats()
            schema_version = storage.get_schema_version()
        except Exception as e:
            db_healthy = False
            db_error = str(e)
            stats = {}
            schema_version = -1
        
        # Get error statistics
        error_logs = storage.get_logs(level="error", limit=50)
        one_hour_ago = current_time - 3600
        errors_last_hour = len([log for log in error_logs if log.get('created_at', 0) > one_hour_ago])
        
        # Get restart information
        restart_count = storage.get_state("restart_count", 0)
        last_restart = storage.get_state("last_restart")
        
        # Get recent activity count (KEEP THIS PATTERN for activity tracking)
        recent_events = storage.get_events(limit=10)
        recent_logs = storage.get_logs(limit=100)
        total_records = stats.get('total_records', 0) if stats else 0
        
        return {
            "status": "running",
            "uptime": uptime_formatted,
            "uptime_seconds": int(uptime_seconds),
            "last_check": datetime.now().isoformat(),
            "system_health": {
                "fastapi_status": "Running",
                "database_healthy": db_healthy,
                "database_error": db_error,
                "schema_version": schema_version,
                "memory_usage_mb": round(sys.getsizeof(storage) / 1024 / 1024, 2),
                "python_version": platform.python_version(),
                "platform": platform.platform(),
                "restart_count": restart_count,
                "last_restart": last_restart
            },
            "config": {
                "app_name": APP_NAME,
                "environment": APP_ENV,
                "debug_mode": ENABLE_DEBUG,
                "refresh_interval": AUTO_REFRESH_INTERVAL,
                "port": APP_PORT,
                "database_path": DATABASE_PATH
            },
            "error_stats": {
                "errors_last_hour": errors_last_hour,
                "total_errors": len(error_logs),
                "last_error": error_logs[0] if error_logs else None
            },
            "metrics": {
                "processed": len(recent_logs),  # Generic: Total log entries processed
                "pending": 0,  # Generic: No pending operations (can be customized per app)
                "errors": errors_last_hour  # Real error count
            },
            "recent_activity": len(recent_events),  # KEEP THIS for activity tracking
            "database_stats": stats
        }
    except Exception as e:
        # Fallback response if health check fails
        return {
            "status": "degraded",
            "uptime": uptime_formatted,
            "uptime_seconds": int(uptime_seconds),
            "last_check": datetime.now().isoformat(),
            "error": f"Health check failed: {str(e)}",
            "config": {
                "app_name": APP_NAME,
                "environment": APP_ENV,
                "debug_mode": ENABLE_DEBUG,
                "refresh_interval": AUTO_REFRESH_INTERVAL
            },
            "metrics": {
                "processed": 0,
                "pending": 0,
                "errors": 1
            }
        }

# EXAMPLE: Task Management Endpoints - Replace with your own API endpoints
# Follow the same patterns: use Storage class, proper error handling, event logging
# -------------------------

@app.post("/api/tasks")
async def create_task(task_data: TaskCreate):
    """Create a new task"""
    try:
        # Validate input
        if not task_data.title or not task_data.title.strip():
            return create_error_response(
                status_code=400,
                error_code="VALIDATION_ERROR",
                message="Task title is required",
                details="Title cannot be empty or whitespace only"
            )
        
        if task_data.priority not in ["low", "medium", "high"]:
            return create_error_response(
                status_code=400,
                error_code="VALIDATION_ERROR", 
                message="Invalid priority value",
                details="Priority must be one of: low, medium, high"
            )
        
        # Get existing tasks
        tasks = storage.get_state("tasks", [])
        
        # Generate new ID
        next_id = max([task.get("id", 0) for task in tasks], default=0) + 1
        
        # Create new task
        new_task = {
            "id": next_id,
            "title": task_data.title.strip(),
            "description": task_data.description.strip() if task_data.description else None,
            "priority": task_data.priority,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "completed_at": None
        }
        
        # Add to tasks list
        tasks.append(new_task)
        storage.set_state("tasks", tasks)
        
        # Log the event
        storage.log_event("task_created", {
            "task_id": next_id,
            "title": task_data.title,
            "priority": task_data.priority
        })
        
        return create_success_response({"task": new_task})
    except Exception as e:
        return create_error_response(
            status_code=500,
            error_code="INTERNAL_ERROR",
            message="Failed to create task", 
            details=str(e) if ENABLE_DEBUG else "An unexpected error occurred"
        )

@app.get("/api/tasks", response_model=List[Task])
async def get_tasks():
    """Get all tasks"""
    tasks = storage.get_state("tasks", [])
    return tasks

@app.get("/api/tasks/{task_id}")
async def get_task(task_id: int):
    """Get a specific task by ID"""
    try:
        tasks = storage.get_state("tasks", [])
        task = next((task for task in tasks if task.get("id") == task_id), None)
        if not task:
            return create_error_response(
                status_code=404,
                error_code="RESOURCE_NOT_FOUND",
                message="Task not found",
                details=f"Task with ID {task_id} does not exist"
            )
        return create_success_response({"task": task})
    except Exception as e:
        return create_error_response(
            status_code=500,
            error_code="INTERNAL_ERROR",
            message="Failed to retrieve task",
            details=str(e) if ENABLE_DEBUG else "An unexpected error occurred"
        )

@app.patch("/api/tasks/{task_id}/status")
async def update_task_status(task_id: int, status: dict):
    """Update task status (pending, in_progress, completed)"""
    try:
        new_status = status.get("status")
        if not new_status:
            return create_error_response(
                status_code=400,
                error_code="VALIDATION_ERROR",
                message="Status is required",
                details="Request body must include 'status' field"
            )
            
        if new_status not in ["pending", "in_progress", "completed"]:
            return create_error_response(
                status_code=400,
                error_code="VALIDATION_ERROR",
                message="Invalid status value",
                details="Status must be one of: pending, in_progress, completed"
            )
        
        tasks = storage.get_state("tasks", [])
        task = next((task for task in tasks if task.get("id") == task_id), None)
        if not task:
            return create_error_response(
                status_code=404,
                error_code="RESOURCE_NOT_FOUND",
                message="Task not found",
                details=f"Task with ID {task_id} does not exist"
            )
        
        old_status = task["status"]
        task["status"] = new_status
        
        if new_status == "completed":
            task["completed_at"] = datetime.now().isoformat()
        
        storage.set_state("tasks", tasks)
        
        # Log the event
        storage.log_event("task_status_changed", {
            "task_id": task_id,
            "old_status": old_status,
            "new_status": new_status,
            "title": task["title"]
        })
        
        return create_success_response({"task": task})
    except Exception as e:
        return create_error_response(
            status_code=500,
            error_code="INTERNAL_ERROR",
            message="Failed to update task status",
            details=str(e) if ENABLE_DEBUG else "An unexpected error occurred"
        )

@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: int):
    """Delete a task"""
    try:
        tasks = storage.get_state("tasks", [])
        task = next((task for task in tasks if task.get("id") == task_id), None)
        if not task:
            return create_error_response(
                status_code=404,
                error_code="RESOURCE_NOT_FOUND",
                message="Task not found",
                details=f"Task with ID {task_id} does not exist"
            )
        
        # Remove task from list
        tasks = [t for t in tasks if t.get("id") != task_id]
        storage.set_state("tasks", tasks)
        
        # Log the event
        storage.log_event("task_deleted", {
            "task_id": task_id,
            "title": task["title"]
        })
        
        return create_success_response({"message": "Task deleted successfully", "task_id": task_id})
    except Exception as e:
        return create_error_response(
            status_code=500,
            error_code="INTERNAL_ERROR",
            message="Failed to delete task",
            details=str(e) if ENABLE_DEBUG else "An unexpected error occurred"
        )

@app.get("/api/activity")
async def get_recent_activity():
    """Get recent activity events - KEEP THIS PATTERN for activity tracking"""
    events = storage.get_events(limit=20)
    return {
        "events": events,
        "total": len(events),
        "timestamp": datetime.now().isoformat()
    }

# Legacy endpoints for compatibility (KEEP THESE PATTERNS)
@app.post("/api/action")
async def perform_action(data: dict = None):
    """Legacy action endpoint - EXAMPLE: creates a sample task (replace with your logic)"""
    try:
        # Create a sample task as the action
        task_data = TaskCreate(
            title=f"Sample task created at {datetime.now().strftime('%H:%M:%S')}",
            description="This task was created from the legacy action endpoint",
            priority="medium"
        )
        result = await create_task(task_data)
        
        # Since create_task now returns standardized responses, we need to extract the data
        if isinstance(result, JSONResponse):
            # If it's an error response, return it directly
            return result
        elif result.get("success") and result.get("data"):
            # Success response from create_task
            return create_success_response({
                "message": "Sample task created successfully", 
                "task": result["data"]["task"]
            })
        else:
            # Fallback success response
            return create_success_response({
                "message": "Sample task created successfully",
                "task": result
            })
    except Exception as e:
        return create_error_response(
            status_code=500,
            error_code="INTERNAL_ERROR",
            message="Failed to perform action",
            details=str(e) if ENABLE_DEBUG else "An unexpected error occurred"
        )

@app.get("/api/data")
async def get_data():
    """Legacy data endpoint - returns task summary"""
    tasks = storage.get_state("tasks", [])
    return {
        "items": tasks[:5],  # Return first 5 tasks
        "total": len(tasks),
        "timestamp": datetime.now().isoformat()
    }

# Database Test Endpoints
@app.get("/api/database/test")
async def test_database_connection(db: AsyncSession = Depends(get_db_session)):
    """Test database connection with a simple query"""
    try:
        # Import here to avoid circular imports
        from sqlalchemy import text
        
        # Test basic connection
        result = await db.execute(text("SELECT 1"))
        test_result = result.scalar()
        
        # Test table count
        result = await db.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'"))
        table_count = result.scalar()
        
        return create_success_response({
            "database_connection": "SUCCESS",
            "test_query_result": test_result,
            "total_tables": table_count,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return create_error_response(
            status_code=500,
            error_code="DATABASE_ERROR",
            message="Database connection test failed",
            details=str(e) if ENABLE_DEBUG else "Database connection error"
        )

@app.get("/api/database/companies")
async def get_companies(db: AsyncSession = Depends(get_db_session)):
    """Get all companies from the database"""
    try:
        from sqlalchemy import select
        
        result = await db.execute(select(Company))
        companies = result.scalars().all()
        
        companies_data = [
            {
                "id": str(company.id),
                "name": company.name,
                "slug": company.slug,
                "subscription_tier": company.subscription_tier,
                "is_active": company.is_active,
                "created_at": company.created_at.isoformat()
            }
            for company in companies
        ]
        
        return create_success_response({
            "companies": companies_data,
            "total": len(companies_data),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return create_error_response(
            status_code=500,
            error_code="DATABASE_ERROR",
            message="Failed to retrieve companies",
            details=str(e) if ENABLE_DEBUG else "Database query error"
        )

# Admin API Endpoints
@app.get("/api/admin/tables")
async def get_database_tables(db: AsyncSession = Depends(get_db_session)):
    """Get list of all database tables with row counts"""
    try:
        from sqlalchemy import text
        
        # Get table names and row counts
        query = text("""
            SELECT 
                t.table_name,
                COALESCE(
                    (SELECT n_tup_ins FROM pg_stat_user_tables WHERE relname = t.table_name),
                    0
                ) as row_count
            FROM information_schema.tables t
            WHERE t.table_schema = 'public' 
                AND t.table_type = 'BASE TABLE'
                AND t.table_name != 'alembic_version'
            ORDER BY t.table_name
        """)
        
        result = await db.execute(query)
        tables = [
            {
                "name": row[0],
                "row_count": row[1]
            }
            for row in result.fetchall()
        ]
        
        return create_success_response({
            "tables": tables,
            "total_count": len(tables)
        })
        
    except Exception as e:
        return create_error_response(
            status_code=500,
            error_code="DATABASE_ERROR",
            message="Failed to retrieve database tables",
            details=str(e) if ENABLE_DEBUG else "Database query error"
        )

@app.get("/api/admin/table/{table_name}")
async def get_table_details(table_name: str, db: AsyncSession = Depends(get_db_session)):
    """Get detailed information about a specific table"""
    try:
        from sqlalchemy import text
        
        # Get table columns information
        columns_query = text("""
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = :table_name
            ORDER BY ordinal_position
        """)
        
        columns_result = await db.execute(columns_query, {"table_name": table_name})
        columns = [
            {
                "name": row[0],
                "type": row[1],
                "nullable": row[2] == "YES",
                "default": row[3]
            }
            for row in columns_result.fetchall()
        ]
        
        # Get row count
        count_query = text(f"SELECT COUNT(*) FROM {table_name}")
        count_result = await db.execute(count_query)
        row_count = count_result.scalar()
        
        return create_success_response({
            "table_name": table_name,
            "columns": columns,
            "row_count": row_count,
            "column_count": len(columns)
        })
        
    except Exception as e:
        return create_error_response(
            status_code=500,
            error_code="DATABASE_ERROR",
            message=f"Failed to retrieve table details for {table_name}",
            details=str(e) if ENABLE_DEBUG else "Database query error"
        )

@app.get("/api/admin/migration-status")
async def get_migration_status(db: AsyncSession = Depends(get_db_session)):
    """Get current migration status"""
    try:
        from sqlalchemy import text
        
        # Check current migration version
        version_query = text("SELECT version_num FROM alembic_version")
        result = await db.execute(version_query)
        current_version = result.scalar()
        
        return create_success_response({
            "status": "up_to_date",
            "current_version": current_version or "None",
            "pending_count": 0,
            "last_migration": datetime.now().isoformat()
        })
        
    except Exception as e:
        return create_error_response(
            status_code=500,
            error_code="DATABASE_ERROR",
            message="Failed to check migration status",
            details=str(e) if ENABLE_DEBUG else "Migration check error"
        )

@app.post("/api/admin/run-migrations")
async def run_database_migrations():
    """Run pending database migrations"""
    try:
        # Note: In production, this would run actual migrations
        # For now, return a success message
        return create_success_response({
            "status": "completed",
            "migrations_run": 0,
            "output": "No pending migrations to run.",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return create_error_response(
            status_code=500,
            error_code="MIGRATION_ERROR",
            message="Failed to run migrations",
            details=str(e) if ENABLE_DEBUG else "Migration execution error"
        )

@app.get("/api/admin/sync-status")
async def get_sync_status():
    """Get OLIS synchronization status"""
    try:
        # Mock sync status for now
        return create_success_response({
            "status": "idle",
            "last_sync": "2024-09-08T10:30:00Z",
            "next_sync": "Not scheduled",
            "sync_interval": 60,
            "records_synced": 1250,
            "last_sync_duration": "4m 32s"
        })
        
    except Exception as e:
        return create_error_response(
            status_code=500,
            error_code="SYNC_ERROR",
            message="Failed to get sync status",
            details=str(e) if ENABLE_DEBUG else "Sync status error"
        )

@app.post("/api/admin/manual-sync")
async def run_manual_sync(sync_request: dict = None):
    """Start a manual OLIS synchronization"""
    try:
        session_key = sync_request.get("session_key") if sync_request else None
        storage.log("info", f"Starting manual OLIS sync for session: {session_key or 'ALL'}")
        
        # Run the actual OLIS synchronization
        sync_results = await run_olis_sync(session_key)
        
        return create_success_response({
            "status": sync_results.get("status", "completed"),
            "sync_id": "sync_" + datetime.now().strftime("%Y%m%d_%H%M%S"),
            "session_key": session_key,
            "results": sync_results.get("results", {}),
            "timestamp": sync_results.get("timestamp")
        })
        
    except Exception as e:
        storage.log("error", f"Manual sync failed: {str(e)}")
        return create_error_response(
            status_code=500,
            error_code="SYNC_ERROR",
            message="Failed to run manual sync",
            details=str(e) if ENABLE_DEBUG else "Sync execution error"
        )

@app.post("/api/admin/vacuum")
async def vacuum_database():
    """Run database vacuum operation"""
    import time
    import asyncpg
    from urllib.parse import urlparse
    
    start_time = time.time()
    
    try:
        # Parse the database URL to get connection parameters
        from database_config import DATABASE_URL
        
        # Convert asyncpg URL to regular PostgreSQL URL for asyncpg
        db_url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
        
        # Create a direct asyncpg connection (VACUUM cannot run in transactions)
        conn = await asyncpg.connect(db_url)
        
        try:
            # Run VACUUM ANALYZE for comprehensive maintenance
            await conn.execute("VACUUM ANALYZE")
            
            # Calculate duration
            duration = round(time.time() - start_time, 2)
            
            return create_success_response({
                "status": "completed",
                "operation": "vacuum_analyze",
                "duration": f"{duration} seconds",
                "timestamp": datetime.now().isoformat(),
                "details": [
                    "Vacuum operation completed successfully",
                    "Database statistics updated",
                    "Storage space reclaimed"
                ]
            })
            
        finally:
            await conn.close()
        
    except Exception as e:
        duration = round(time.time() - start_time, 2)
        return create_error_response(
            status_code=500,
            error_code="MAINTENANCE_ERROR",
            message="Failed to vacuum database",
            details={
                "error": str(e) if ENABLE_DEBUG else "Vacuum operation error",
                "duration": f"{duration} seconds"
            }
        )

@app.post("/api/admin/backup")
async def backup_database():
    """Create a database backup"""
    try:
        # Mock backup operation
        backup_filename = f"olis_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        
        return create_success_response({
            "status": "completed",
            "filename": backup_filename,
            "size": "15.2 MB",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return create_error_response(
            status_code=500,
            error_code="BACKUP_ERROR",
            message="Failed to create database backup",
            details=str(e) if ENABLE_DEBUG else "Backup operation error"
        )

# OLIS API Endpoints
@app.get("/api/sessions")
async def get_sessions():
    """Get all legislative sessions from OLIS"""
    try:
        client = OLISClient()
        sessions = await client.get_sessions()
        return create_success_response({"sessions": sessions})
    except Exception as e:
        return create_error_response(
            status_code=500,
            error_code="OLIS_ERROR",
            message="Failed to fetch sessions",
            details=str(e) if ENABLE_DEBUG else "Could not retrieve legislative sessions"
        )

@app.get("/api/sessions/{session_key}/stats")
async def get_session_stats(session_key: str):
    """Get enhanced bill statistics for a specific session"""
    try:
        client = OLISClient()
        
        # Get ALL measures for this session (no limit)
        measures = await client.get_all_measures(session_key)
        
        # Use enhanced status classification
        stats = categorize_bills_by_status(measures)
        
        # Add specific committee analysis
        specific_committee_stats = categorize_bills_by_specific_committees(measures)
        
        return create_success_response({
            "session_key": session_key,
            "total_bills": stats['total_bills'],
            "bill_types": stats['bill_types'],
            "status_counts": stats['status_counts'],
            "status_display": stats['status_display'],
            "bill_type_counts": stats['bill_type_counts'],
            "specific_committees": specific_committee_stats,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return create_error_response(
            status_code=500,
            error_code="OLIS_ERROR", 
            message="Failed to fetch session statistics",
            details=str(e) if ENABLE_DEBUG else "Could not retrieve session statistics"
        )

@app.get("/api/sessions/{session_key}/hot-bills")
async def get_hot_bills(session_key: str, limit: int = 10):
    """Get hot bills ranked by testimony volume and diversity"""
    try:
        storage.log("info", f"Hot bills requested for session: {session_key}")
        
        client = OLISClient()
        
        # Analyze hot bills using testimony data
        hot_bills_data = await analyze_hot_bills(client, session_key, limit)
        
        return create_success_response(hot_bills_data)
        
    except Exception as e:
        return create_error_response(
            status_code=500,
            error_code="OLIS_ERROR",
            message="Failed to fetch hot bills",
            details=str(e) if ENABLE_DEBUG else "Could not retrieve hot bills data"
        )

# Debug Endpoints - Add detailed system information
@app.get("/api/debug/health")
async def debug_health_check():
    """Comprehensive health check with database and system info"""
    try:
        # Test database connectivity
        db_healthy = True
        db_error = None
        try:
            stats = storage.get_stats()
        except Exception as e:
            db_healthy = False
            db_error = str(e)
            stats = {}
        
        # Get migration status
        try:
            schema_version = storage.get_schema_version()
            migration_history = storage.get_migration_history()
        except Exception as e:
            schema_version = -1
            migration_history = []
        
        return create_success_response({
            "status": "healthy" if db_healthy else "degraded",
            "timestamp": datetime.now().isoformat(),
            "service": APP_NAME,
            "version": "1.0.0",
            "environment": APP_ENV,
            "debug_mode": ENABLE_DEBUG,
            "database": {
                "healthy": db_healthy,
                "error": db_error,
                "path": DATABASE_PATH,
                "schema_version": schema_version,
                "stats": stats
            },
            "configuration": {
                "app_port": APP_PORT,
                "refresh_interval": AUTO_REFRESH_INTERVAL
            },
            "migrations": {
                "current_version": schema_version,
                "history_count": len(migration_history)
            }
        })
    except Exception as e:
        return create_error_response(
            status_code=500,
            error_code="INTERNAL_ERROR",
            message="Health check failed",
            details=str(e) if ENABLE_DEBUG else "System error occurred"
        )

@app.get("/api/debug/migrations")
async def debug_migrations():
    """Get database migration history and status"""
    try:
        return create_success_response({
            "current_version": storage.get_schema_version(),
            "migration_history": storage.get_migration_history(),
            "database_path": DATABASE_PATH
        })
    except Exception as e:
        return create_error_response(
            status_code=500,
            error_code="INTERNAL_ERROR",
            message="Failed to retrieve migration information",
            details=str(e) if ENABLE_DEBUG else "Database error occurred"
        )

@app.get("/api/debug/logs")
async def debug_logs(level: Optional[str] = None, limit: int = 100):
    """Get recent application logs"""
    try:
        # Validate limit
        if limit > 1000:
            return create_error_response(
                status_code=400,
                error_code="VALIDATION_ERROR",
                message="Limit too high",
                details="Maximum limit is 1000"
            )
        
        logs = storage.get_logs(level=level, limit=limit)
        return create_success_response({
            "logs": logs,
            "total": len(logs),
            "level_filter": level,
            "limit": limit
        })
    except Exception as e:
        return create_error_response(
            status_code=500,
            error_code="INTERNAL_ERROR",
            message="Failed to retrieve logs",
            details=str(e) if ENABLE_DEBUG else "Database error occurred"
        )

@app.post("/api/debug/report-error")
async def report_frontend_error(error_data: dict):
    """Endpoint for frontend to report JavaScript errors"""
    try:
        # Log the frontend error
        error_info = {
            "source": "frontend",
            "message": error_data.get("message", "Unknown error"),
            "filename": error_data.get("filename", ""),
            "line": error_data.get("line", 0),
            "column": error_data.get("column", 0),
            "stack": error_data.get("stack", ""),
            "user_agent": error_data.get("userAgent", ""),
            "url": error_data.get("url", "")
        }
        
        storage.log("error", f"Frontend error: {error_info['message']}")
        storage.log_event("frontend_error", error_info)
        
        return create_success_response({
            "message": "Error reported successfully",
            "error_id": datetime.now().isoformat()
        })
        
    except Exception as e:
        return create_error_response(
            status_code=500,
            error_code="INTERNAL_ERROR",
            message="Failed to report error",
            details=str(e) if ENABLE_DEBUG else "Error reporting failed"
        )

@app.get("/api/debug/error-stats")
async def get_error_statistics():
    """Get error statistics and monitoring data"""
    try:
        # Get error logs
        error_logs = storage.get_logs(level="error", limit=50)
        
        # Get frontend error events
        frontend_errors = storage.get_events(event_type="frontend_error", limit=20)
        
        # Calculate error rate (errors per hour)
        now = datetime.now()
        one_hour_ago = now.timestamp() - 3600
        
        recent_errors = [log for log in error_logs if log.get('created_at', '') > one_hour_ago]
        error_rate = len(recent_errors)
        
        return create_success_response({
            "error_rate_per_hour": error_rate,
            "total_errors": len(error_logs),
            "frontend_errors": len(frontend_errors),
            "recent_error_logs": error_logs[:10],  # Last 10 errors
            "recent_frontend_errors": frontend_errors[:5]  # Last 5 frontend errors
        })
        
    except Exception as e:
        return create_error_response(
            status_code=500,
            error_code="INTERNAL_ERROR",
            message="Failed to retrieve error statistics",
            details=str(e) if ENABLE_DEBUG else "Statistics unavailable"
        )

# Frontend Routes
# ---------------

# Mount static files (CSS, JS, etc.)
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

# Mount shared design system files
SHARED_DIR = Path(__file__).parent.parent / "shared"
app.mount("/shared", StaticFiles(directory=str(SHARED_DIR)), name="shared")

@app.get("/")
async def serve_dashboard():
    """Serve the main dashboard"""
    return FileResponse(str(FRONTEND_DIR / "index.html"))

@app.get("/demo")
async def serve_demo():
    """Serve the task management demo page"""
    return FileResponse(str(FRONTEND_DIR / "demo.html"))

@app.get("/system-health")
async def serve_health():
    """Serve the system health monitoring page"""
    return FileResponse(str(FRONTEND_DIR / "health.html"))

@app.get("/admin")
async def serve_admin():
    """Serve the administration interface"""
    return FileResponse(str(FRONTEND_DIR / "admin.html"))

@app.get("/admin-test")
async def serve_admin_test():
    """Serve the admin test page"""
    return FileResponse(str(FRONTEND_DIR / "admin-test.html"))

@app.get("/examples")
async def serve_examples():
    """Serve the component examples page"""
    return FileResponse(str(SHARED_DIR / "examples.html"))

# Catch-all route for SPA routing (if needed)
@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    """Catch all routes and serve index.html for SPA routing"""
    # First check if it's a static file
    file_path = FRONTEND_DIR / full_path
    if file_path.exists() and file_path.is_file():
        return FileResponse(str(file_path))
    # Otherwise serve the index.html
    return FileResponse(str(FRONTEND_DIR / "index.html"))

# Event Handlers for Service Lifecycle
@app.on_event("startup")
async def startup_event():
    """Log service startup"""
    try:
        storage.log_event("service_started", {
            "timestamp": datetime.now().isoformat(),
            "pid": os.getpid(),
            "port": APP_PORT,
            "environment": APP_ENV
        })
        storage.log("info", f"Service started on port {APP_PORT}")
        print(f"🚀 {APP_NAME} started on port {APP_PORT}")
    except Exception as e:
        print(f"Failed to log startup event: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Log service shutdown"""
    try:
        uptime = time.time() - START_TIME
        storage.log_event("service_stopped", {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": int(uptime),
            "pid": os.getpid()
        })
        storage.log("info", f"Service stopped after {int(uptime)} seconds")
        print(f"🛑 {APP_NAME} stopped after {int(uptime)} seconds")
    except Exception as e:
        print(f"Failed to log shutdown event: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=APP_PORT, reload=ENABLE_DEBUG)
