from django.db import migrations, models
import django.db.models.deletion


def copy_usernames(apps, schema_editor):
    LoginAttempt = apps.get_model("authentication", "LoginAttempt")
    for attempt in LoginAttempt.objects.select_related("user"):
        if attempt.user_id and not attempt.username:
            attempt.username = attempt.user.username
            attempt.save(update_fields=["username"])


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0002_alter_user_role"),
    ]

    operations = [
        migrations.AddField(
            model_name="loginattempt",
            name="username",
            field=models.CharField(db_index=True, default="", max_length=150),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="loginattempt",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="login_attempts",
                to="authentication.user",
            ),
        ),
        migrations.RunPython(copy_usernames, migrations.RunPython.noop),
    ]
