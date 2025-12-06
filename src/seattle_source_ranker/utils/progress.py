"""
Progress monitoring utilities for long-running tasks
"""
import time
import sys
from typing import Optional


class ProgressMonitor:
    """Unified progress bar monitor for long-running tasks"""
    
    def __init__(self, total: int, desc: str = "Processing", bar_length: int = 40):
        """
        Args:
            total: Total number of tasks
            desc: Description text
            bar_length: Length of progress bar
        """
        self.total = total
        self.desc = desc
        self.bar_length = bar_length
        self.start_time = time.time()
        self.last_completed = 0
        self.last_print_time = 0
        self.first_task_started = False
        
    def update(self, completed: int, force: bool = False):
        """
        Update progress
        
        Args:
            completed: Number of completed tasks
            force: Force update regardless of change
        """
        current_time = time.time()
        
        # Check if should print
        should_print = completed > self.last_completed or force
        
        # Or print every 5 seconds if no progress (heartbeat)
        if not should_print and (current_time - self.last_print_time) >= 5:
            should_print = True
        
        if not should_print:
            return
        
        # Reset start time when first task completes
        if completed > 0 and not self.first_task_started:
            self.first_task_started = True
            self.start_time = current_time
        
        if not self.first_task_started:
            # Still waiting for first task
            elapsed = int(current_time - self.start_time)
            print(f"\r   {self.desc}: Waiting for workers to start... ({elapsed}s elapsed)", 
                  end='', flush=True)
        else:
            # Tasks processing
            # Ensure completed doesn't exceed total
            completed_capped = min(completed, self.total)
            
            percent = (completed_capped / self.total) * 100 if self.total > 0 else 0
            elapsed = current_time - self.start_time
            rate = completed / elapsed if elapsed > 0 else 0
            remaining = self.total - completed
            eta = remaining / rate if rate > 0 else 0
            
            # Progress bar - use capped value for display
            filled = int(self.bar_length * completed_capped / self.total) if self.total > 0 else 0
            bar = '█' * filled + '░' * (self.bar_length - filled)
            
            print(f"\r   [{bar}] {completed}/{self.total} ({percent:.1f}%) | "
                  f"Rate: {rate:.1f}/s | ETA: {eta:.0f}s", end='', flush=True)
        
        self.last_completed = completed
        self.last_print_time = current_time
    
    def finish(self):
        """Finish progress bar with newline"""
        print()  # New line
        
    def get_elapsed(self) -> float:
        """Get elapsed time in seconds"""
        return time.time() - self.start_time


def monitor_celery_task(result, total_tasks: int, desc: str = "Processing", 
                        check_interval: float = 1.0, timeout: Optional[int] = None):
    """
    Monitor Celery GroupResult and display progress
    
    Args:
        result: Celery GroupResult
        total_tasks: Total number of tasks
        desc: Task description
        check_interval: Check interval in seconds
        timeout: Timeout in seconds, None for no timeout
        
    Returns:
        List of task results
        
    Raises:
        Exception: If task fails
        TimeoutError: If timeout occurs
    """
    progress = ProgressMonitor(total_tasks, desc)
    start_time = time.time()
    
    try:
        while not result.ready():
            completed = result.completed_count()
            progress.update(completed)
            
            # Check timeout
            if timeout and (time.time() - start_time) > timeout:
                raise TimeoutError(f"Task timeout after {timeout}s")
            
            time.sleep(check_interval)
        
        # Ensure final progress bar shows 100%
        progress.update(total_tasks, force=True)
        progress.finish()
        
        # Get results (will raise exception if task failed)
        print(f"\n[STATS] Collecting results...")
        try:
            results = result.get()
            return results
        except Exception as e:
            print(f"\n[FATAL ERROR] Task failed: {e}")
            print("[ABORT] Data collection/verification incomplete")
            raise
            
    except KeyboardInterrupt:
        progress.finish()
        print("\n[INTERRUPT] Task cancelled by user")
        raise
