from django.conf import settings
from django.db import models


class Vote(models.Model):
    voter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="votes",
    )
    candidate = models.ForeignKey(
        "candidates.Candidate",
        on_delete=models.CASCADE,
        related_name="votes",
    )
    voted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "voting_vote"
        constraints = [
            models.UniqueConstraint(fields=["voter"], name="unique_vote_per_voter"),
        ]
