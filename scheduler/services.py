from django.utils import timezone
from django.db.models import Q, F
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging

from .models import ScheduledTask, UserAvailability, SchedulingSession
from goals.models import Goal, Task

logger = logging.getLogger(__name__)

class SchedulingService:
    """
    Deterministic, real-time, rule-based AI scheduling system
    
    Features:
    - Weighted scoring based on urgency, importance, and progress
    - Constraint-based greedy scheduling
    - Real-time adaptation to user actions
    - Dependency enforcement for sub-goals
    """
    
    def __init__(self, user):
        self.user = user
        self.now = timezone.now()
    
    def get_all_tasks_for_user(self) -> List[Task]:
        """Get all tasks for the user, including those from goals and sub-goals"""
        # Get all goals for the user (including sub-goals)
        user_goals = Goal.objects.filter(user=self.user)
        
        # Get all tasks from these goals
        tasks = Task.objects.filter(goal__in=user_goals).exclude(
            status__in=['completed', 'cancelled']
        )
        
        return list(tasks)
    
    def calculate_task_priority(self, task: Task) -> float:
        """
        Calculate priority score using the AI algorithm:
        Priority = (Urgency * 0.4) + (Importance * 0.4) + (Progress * 0.2)
        """
        # Calculate urgency (1 / (days_left_to_deadline + 1))
        urgency = 0.0
        if task.due_date:
            days_left = (task.due_date - self.now).days
            urgency = 1.0 / (max(days_left, 0) + 1)
        else:
            urgency = 0.1  # Low urgency for tasks without deadline
        
        # Calculate importance (priority level)
        priority_map = {'high': 3.0, 'medium': 2.0, 'low': 1.0}
        importance = priority_map.get(task.goal.priority, 2.0)
        
        # Calculate progress (1 - progress_percentage)
        progress = 1.0 - (task.goal.progress / 100.0)
        
        # Calculate final weighted score
        final_score = (urgency * 0.4) + (importance * 0.4) + (progress * 0.2)
        
        return final_score
    
    def get_dependency_order(self, tasks: List[Task]) -> List[Task]:
        """
        Sort tasks by dependency order (sub-goals before parent goals)
        Returns tasks in order where dependencies are satisfied
        """
        # Create a mapping of goal dependencies
        goal_dependencies = {}
        for task in tasks:
            goal = task.goal
            dependencies = []
            
            # Check if this goal has parent goals that need to be completed first
            current_goal = goal
            while current_goal.parent:
                parent_goal = current_goal.parent
                # If parent goal is not completed, it's a dependency
                if parent_goal.status != 'completed':
                    parent_tasks = [t for t in tasks if t.goal == parent_goal]
                    dependencies.extend(parent_tasks)
                current_goal = parent_goal
            
            goal_dependencies[task] = dependencies
        
        # Topological sort to respect dependencies
        sorted_tasks = []
        visited = set()
        temp_visited = set()
        
        def visit(task):
            if task in temp_visited:
                raise ValueError("Circular dependency detected")
            if task in visited:
                return
            
            temp_visited.add(task)
            
            # Visit dependencies first
            for dep in goal_dependencies[task]:
                visit(dep)
            
            temp_visited.remove(task)
            visited.add(task)
            sorted_tasks.append(task)
        
        # Visit all tasks
        for task in tasks:
            if task not in visited:
                visit(task)
        
        return sorted_tasks
    
    def get_user_availability(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """
        Get user's available time slots between start_date and end_date
        Returns list of available time slots
        """
        availabilities = UserAvailability.objects.filter(
            user=self.user,
            is_active=True
        )
        
        available_slots = []
        current_date = start_date.date()
        end_date_only = end_date.date()
        
        while current_date <= end_date_only:
            day_of_week = current_date.weekday()
            day_availabilities = availabilities.filter(day_of_week=day_of_week)
            
            for availability in day_availabilities:
                slot_start = datetime.combine(current_date, availability.start_time)
                slot_end = datetime.combine(current_date, availability.end_time)
                
                # Adjust for timezone
                slot_start = timezone.make_aware(slot_start)
                slot_end = timezone.make_aware(slot_end)
                
                # Only include slots that overlap with our date range
                if slot_start < end_date and slot_end > start_date:
                    available_slots.append({
                        'start': slot_start,
                        'end': slot_end,
                        'duration_minutes': (slot_end - slot_start).total_seconds() / 60
                    })
            
            current_date += timedelta(days=1)
        
        return available_slots
    
    def schedule_tasks(self, tasks: List[Task], start_date: datetime = None, 
                      end_date: datetime = None) -> List[ScheduledTask]:
        """
        Main scheduling function using constraint-based greedy algorithm
        
        Args:
            tasks: List of tasks to schedule
            start_date: Start date for scheduling (defaults to now)
            end_date: End date for scheduling (defaults to 7 days from now)
        
        Returns:
            List of ScheduledTask objects
        """
        if not tasks:
            return []
        
        # Set default date range if not provided
        if not start_date:
            start_date = self.now
        if not end_date:
            end_date = self.now + timedelta(days=7)
        
        # Get dependency-ordered tasks
        ordered_tasks = self.get_dependency_order(tasks)
        
        # Calculate priority scores and sort by descending priority
        task_scores = []
        for task in ordered_tasks:
            priority_score = self.calculate_task_priority(task)
            task_scores.append((task, priority_score))
        
        # Sort by descending priority score
        task_scores.sort(key=lambda x: x[1], reverse=True)
        sorted_tasks = [task for task, score in task_scores]
        
        # Get available time slots
        available_slots = self.get_user_availability(start_date, end_date)
        
        # Create or update ScheduledTask objects
        scheduled_tasks = []
        current_time = start_date
        
        for task in sorted_tasks:
            # Find the best available slot for this task
            best_slot = self._find_best_slot_for_task(task, available_slots, current_time)
            
            if best_slot:
                # Create or update ScheduledTask
                scheduled_task, created = ScheduledTask.objects.get_or_create(
                    task=task,
                    user=self.user,
                    defaults={
                        'urgency_score': 0.0,
                        'importance_score': 0.0,
                        'progress_score': 0.0,
                        'final_priority_score': 0.0,
                        'status': 'pending'
                    }
                )
                
                # Update priority scores
                scheduled_task.urgency_score = task_scores[sorted_tasks.index(task)][1] * 0.4
                scheduled_task.importance_score = task_scores[sorted_tasks.index(task)][1] * 0.4
                scheduled_task.progress_score = task_scores[sorted_tasks.index(task)][1] * 0.2
                scheduled_task.final_priority_score = task_scores[sorted_tasks.index(task)][1]
                
                # Set scheduling times
                scheduled_task.scheduled_start = best_slot['start']
                scheduled_task.scheduled_end = best_slot['start'] + timedelta(minutes=task.estimated_time)
                
                scheduled_task.save()
                scheduled_tasks.append(scheduled_task)
                
                # Update current time and available slots
                current_time = scheduled_task.scheduled_end
                self._update_available_slots(available_slots, best_slot, task.estimated_time)
        
        # Create scheduling session record
        self._create_scheduling_session(scheduled_tasks)
        
        return scheduled_tasks
    
    def _find_best_slot_for_task(self, task: Task, available_slots: List[Dict], 
                                current_time: datetime) -> Optional[Dict]:
        """Find the best available time slot for a task"""
        task_duration = task.estimated_time
        
        # Filter slots that have enough time for the task
        suitable_slots = [
            slot for slot in available_slots 
            if slot['duration_minutes'] >= task_duration and slot['start'] >= current_time
        ]
        
        if not suitable_slots:
            return None
        
        # Return the earliest suitable slot
        return min(suitable_slots, key=lambda x: x['start'])
    
    def _update_available_slots(self, available_slots: List[Dict], used_slot: Dict, 
                               task_duration: int):
        """Update available slots after scheduling a task"""
        task_end = used_slot['start'] + timedelta(minutes=task_duration)
        
        # Remove or split slots that overlap with the scheduled task
        new_slots = []
        for slot in available_slots:
            if slot['end'] <= used_slot['start'] or slot['start'] >= task_end:
                # No overlap, keep the slot
                new_slots.append(slot)
            else:
                # Overlap detected, split or remove the slot
                if slot['start'] < used_slot['start']:
                    # Keep the part before the task
                    new_slots.append({
                        'start': slot['start'],
                        'end': used_slot['start'],
                        'duration_minutes': (used_slot['start'] - slot['start']).total_seconds() / 60
                    })
                
                if slot['end'] > task_end:
                    # Keep the part after the task
                    new_slots.append({
                        'start': task_end,
                        'end': slot['end'],
                        'duration_minutes': (slot['end'] - task_end).total_seconds() / 60
                    })
        
        available_slots.clear()
        available_slots.extend(new_slots)
    
    def _create_scheduling_session(self, scheduled_tasks: List[ScheduledTask]):
        """Create a record of this scheduling session"""
        total_time = sum(task.task.estimated_time for task in scheduled_tasks)
        
        SchedulingSession.objects.create(
            user=self.user,
            total_tasks_scheduled=len(scheduled_tasks),
            total_time_scheduled=total_time,
            session_notes=f"AI scheduled {len(scheduled_tasks)} tasks with total time {total_time} minutes"
        )
    
    def reschedule_remaining_tasks(self):
        """Reschedule remaining tasks after a task completion or skip"""
        # Get all pending and in-progress scheduled tasks
        remaining_scheduled = ScheduledTask.objects.filter(
            user=self.user,
            status__in=['pending', 'in_progress']
        )
        
        # Get the underlying tasks
        remaining_tasks = [scheduled.task for scheduled in remaining_scheduled]
        
        # Delete existing scheduled tasks
        remaining_scheduled.delete()
        
        # Reschedule the remaining tasks
        if remaining_tasks:
            self.schedule_tasks(remaining_tasks)
    
    def get_high_priority_tasks(self, limit: int = 10) -> List[Dict]:
        """
        Get high priority tasks that are close to due date
        Returns list of task dictionaries with priority scores
        """
        all_tasks = self.get_all_tasks_for_user()
        
        # Calculate priority scores for all tasks
        task_priorities = []
        for task in all_tasks:
            priority_score = self.calculate_task_priority(task)
            task_priorities.append({
                'task': task,
                'priority_score': priority_score,
                'urgency_score': priority_score * 0.4,
                'importance_score': priority_score * 0.4,
                'progress_score': priority_score * 0.2,
                'days_to_deadline': self._get_days_to_deadline(task),
                'goal_name': task.goal.name,
                'estimated_time': task.estimated_time
            })
        
        # Sort by priority score (descending) and limit results
        task_priorities.sort(key=lambda x: x['priority_score'], reverse=True)
        
        return task_priorities[:limit]
    
    def _get_days_to_deadline(self, task: Task) -> Optional[int]:
        """Get days remaining until deadline"""
        if task.due_date:
            return (task.due_date - self.now).days
        return None
    
    def handle_task_completion(self, task: Task):
        """Handle task completion and trigger rescheduling"""
        # Update task status
        task.status = 'completed'
        task.completed_at = self.now
        task.save()
        
        # Update goal progress
        self._update_goal_progress(task.goal)
        
        # Reschedule remaining tasks
        self.reschedule_remaining_tasks()
    
    def handle_task_skip(self, task: Task):
        """Handle task skip and increase urgency"""
        # Update task status
        task.status = 'skipped'
        task.save()
        
        # Increase urgency by moving deadline closer
        if task.due_date:
            task.due_date = task.due_date - timedelta(days=1)
            task.save()
        
        # Reschedule remaining tasks
        self.reschedule_remaining_tasks()
    
    def _update_goal_progress(self, goal: Goal):
        """Update goal progress based on completed tasks"""
        total_tasks = goal.tasks.count()
        completed_tasks = goal.tasks.filter(status='completed').count()
        
        if total_tasks > 0:
            goal.progress = (completed_tasks / total_tasks) * 100.0
            goal.save() 