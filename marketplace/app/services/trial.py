"""Trial lifecycle management for plugin licenses.

Handles starting trials, converting to paid, and expiration.
"""
from datetime import datetime, timedelta, timezone

from flask import current_app

from v_flask import db
from app.models import (
    Project, PluginMeta, License, LicenseHistory,
    LICENSE_STATUS_TRIAL, LICENSE_STATUS_ACTIVE, LICENSE_STATUS_EXPIRED,
)


def start_plugin_trial(
    project_id: int,
    plugin_name: str,
    performed_by: str | None = None
) -> License | None:
    """Start a trial for a plugin.

    Creates a new License with trial status. Trial duration is
    determined by the project's project_type.trial_days.

    Args:
        project_id: ID of the project
        plugin_name: Name of the plugin
        performed_by: Email or identifier of who started the trial

    Returns:
        Created License, or None if trial not allowed.
    """
    project = db.session.get(Project, project_id)
    if not project:
        current_app.logger.warning(f'Project {project_id} not found')
        return None

    plugin = db.session.query(PluginMeta).filter_by(name=plugin_name).first()
    if not plugin:
        current_app.logger.warning(f'Plugin {plugin_name} not found')
        return None

    # Check if plugin supports trial
    if not plugin.has_trial:
        current_app.logger.info(f'Plugin {plugin_name} does not support trial')
        return None

    # Check if license already exists
    existing = db.session.query(License).filter_by(
        project_id=project_id,
        plugin_name=plugin_name
    ).first()
    if existing:
        current_app.logger.info(
            f'License already exists for {project.name}/{plugin_name}'
        )
        return None

    # Determine trial duration
    trial_days = 14  # Default fallback
    if project.project_type:
        trial_days = project.project_type.trial_days

    if trial_days <= 0:
        current_app.logger.info(
            f'No trial allowed for project type {project.project_type.code if project.project_type else "none"}'
        )
        return None

    # Create trial license
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=trial_days)

    license = License(
        project_id=project_id,
        plugin_name=plugin_name,
        status=LICENSE_STATUS_TRIAL,
        billing_cycle='once',
        purchased_at=now,
        expires_at=expires_at,
    )
    db.session.add(license)
    db.session.commit()

    # Log to history
    LicenseHistory.log(
        license_id=license.id,
        action='trial_started',
        new_status=LICENSE_STATUS_TRIAL,
        new_expires_at=expires_at,
        performed_by=performed_by or 'system',
        performed_by_type='customer' if performed_by else 'system',
        extra_data={'trial_days': trial_days},
    )

    current_app.logger.info(
        f'Trial started: {project.name}/{plugin_name} for {trial_days} days'
    )
    return license


def convert_trial_to_paid(
    license_id: int,
    payment_id: str,
    billing_cycle: str = 'once',
    performed_by: str | None = None
) -> License | None:
    """Convert a trial license to paid.

    Called after successful payment to activate the license.

    Args:
        license_id: ID of the trial license
        payment_id: Stripe payment ID or similar
        billing_cycle: New billing cycle (once, monthly, yearly)
        performed_by: Email of who made the payment

    Returns:
        Updated License, or None if conversion failed.
    """
    license = db.session.get(License, license_id)
    if not license:
        current_app.logger.warning(f'License {license_id} not found')
        return None

    if license.status != LICENSE_STATUS_TRIAL:
        current_app.logger.warning(
            f'License {license_id} is not in trial status: {license.status}'
        )
        return None

    old_status = license.status
    old_expires_at = license.expires_at

    # Update license
    license.status = LICENSE_STATUS_ACTIVE
    license.billing_cycle = billing_cycle
    license.stripe_payment_id = payment_id

    # Set new expiration based on billing cycle
    now = datetime.now(timezone.utc)
    if billing_cycle == 'monthly':
        license.expires_at = now + timedelta(days=30)
        license.next_billing_date = license.expires_at
    elif billing_cycle == 'yearly':
        license.expires_at = now + timedelta(days=365)
        license.next_billing_date = license.expires_at
    else:  # once = perpetual
        license.expires_at = None
        license.next_billing_date = None

    db.session.commit()

    # Log to history
    LicenseHistory.log(
        license_id=license.id,
        action='trial_converted',
        old_status=old_status,
        new_status=LICENSE_STATUS_ACTIVE,
        old_expires_at=old_expires_at,
        new_expires_at=license.expires_at,
        old_billing_cycle='once',
        new_billing_cycle=billing_cycle,
        performed_by=performed_by or 'system',
        performed_by_type='customer' if performed_by else 'api',
        extra_data={'payment_id': payment_id},
    )

    current_app.logger.info(f'Trial converted to paid: License {license_id}')
    return license


def expire_trial(
    license_id: int,
    reason: str | None = None
) -> License | None:
    """Expire a trial license.

    Called by scheduler or manually to mark expired trials.

    Args:
        license_id: ID of the license
        reason: Optional reason for expiration

    Returns:
        Updated License, or None if not found.
    """
    license = db.session.get(License, license_id)
    if not license:
        return None

    old_status = license.status
    license.status = LICENSE_STATUS_EXPIRED
    db.session.commit()

    LicenseHistory.log(
        license_id=license.id,
        action='trial_expired',
        old_status=old_status,
        new_status=LICENSE_STATUS_EXPIRED,
        performed_by='system',
        performed_by_type='system',
        reason=reason or 'Trial period ended',
    )

    return license


def get_expiring_trials(days_ahead: int = 3) -> list[License]:
    """Get trials expiring within N days.

    Used for sending reminder notifications.

    Args:
        days_ahead: Number of days to look ahead

    Returns:
        List of License objects expiring soon.
    """
    now = datetime.now(timezone.utc)
    threshold = now + timedelta(days=days_ahead)

    return db.session.query(License).filter(
        License.status == LICENSE_STATUS_TRIAL,
        License.expires_at.isnot(None),
        License.expires_at > now,
        License.expires_at <= threshold,
    ).all()


def get_expired_trials() -> list[License]:
    """Get all expired trials that need status update.

    Returns trials where expires_at has passed but status is still 'trial'.
    """
    now = datetime.now(timezone.utc)

    return db.session.query(License).filter(
        License.status == LICENSE_STATUS_TRIAL,
        License.expires_at.isnot(None),
        License.expires_at < now,
    ).all()


def expire_all_overdue_trials() -> int:
    """Expire all overdue trials.

    Called by a scheduler to batch-expire trials.

    Returns:
        Number of trials expired.
    """
    overdue = get_expired_trials()
    count = 0

    for license in overdue:
        expire_trial(license.id, reason='Automatic expiration')
        count += 1

    return count
