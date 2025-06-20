from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta

class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='time_categories', null=True, blank=True)
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default="#000000")  # Hex color code
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        unique_together = ['user', 'name']

    def __str__(self):
        return self.name

class TimeEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='time_entries', null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Time Entries"
        ordering = ['-start_time']

    def __str__(self):
        return f"{self.description} - {self.start_time}"

    def clean(self):
        if self.end_time and self.start_time and self.start_time >= self.end_time:
            raise ValidationError("End time must be after start time")

    def save(self, *args, **kwargs):
        if self.is_active:
            # Deactivate other active entries
            TimeEntry.objects.filter(
                is_active=True
            ).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    @property
    def duration(self):
        if not self.end_time or not self.start_time:
            return None
        return self.end_time - self.start_time
    