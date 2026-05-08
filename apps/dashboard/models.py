from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    class Action(models.TextChoices):
        LOGIN = "login", "Login"
        LOGOUT = "logout", "Logout"
        VOTE = "vote", "Vote"
        CANDIDATE_REGISTER = "candidate_register", "Candidate Register"
        CANDIDATE_APPROVE = "candidate_approve", "Candidate Approve"
        CANDIDATE_REJECT = "candidate_reject", "Candidate Reject"
        VOTER_CREATE = "voter_create", "Voter Create"
        VOTER_UPDATE = "voter_update", "Voter Update"
        VOTER_DELETE = "voter_delete", "Voter Delete"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=25, choices=Action.choices)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "dashboard_audit_log"
        ordering = ["-timestamp"]
