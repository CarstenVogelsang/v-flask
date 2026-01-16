"""Admin routes for Projektverwaltung plugin.

Blueprint: projektverwaltung_admin
Prefix: /admin/projekte/

Provides routes for administrators to manage:
- Projekte (project containers)
- Komponenten (PRDs/modules/entities)
- Tasks (Kanban board)
- Changelog entries
"""
import re
from datetime import datetime, timezone

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

from v_flask.extensions import db
from v_flask.models import User, Config, LookupWert, Modul
from v_flask.auth.decorators import permission_required

from v_flask_plugins.projektverwaltung.models import (
    Projekt, ProjektTyp,
    Komponente, KomponenteTyp, KomponentePhase, KomponenteStatus,
    Task, TaskStatus, TaskPrioritaet, TaskPhase,
    ChangelogEintrag, ChangelogKategorie, ChangelogSichtbarkeit,
)

admin_bp = Blueprint(
    'projektverwaltung_admin',
    __name__,
    template_folder='../templates'
)


# =============================================================================
# PROJEKTE (Project Containers)
# =============================================================================

@admin_bp.route('/')
@login_required
@permission_required('admin.*')
def index():
    """Dashboard with overview of all projects and components."""
    projekte = Projekt.query.order_by(Projekt.name).all()

    stats = {
        'projekte_intern': sum(1 for p in projekte if p.typ == ProjektTyp.INTERN.value),
        'projekte_kunde': sum(1 for p in projekte if p.typ == ProjektTyp.KUNDE.value),
        'komponenten_total': Komponente.query.count(),
        'tasks_offen': Task.query.filter(Task.status != TaskStatus.ERLEDIGT.value).count(),
        'tasks_in_arbeit': Task.query.filter_by(status=TaskStatus.IN_ARBEIT.value).count(),
    }

    return render_template(
        'projektverwaltung/admin/index.html',
        projekte=projekte,
        stats=stats,
    )


@admin_bp.route('/neu', methods=['GET', 'POST'])
@login_required
@permission_required('admin.*')
def projekt_neu():
    """Create a new project."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        beschreibung = request.form.get('beschreibung', '').strip()
        typ = request.form.get('typ', ProjektTyp.INTERN.value)
        kunde_id = request.form.get('kunde_id', '').strip()

        errors = []
        if not name:
            errors.append('Bitte gib einen Namen ein.')
        if Projekt.query.filter_by(name=name).first():
            errors.append('Ein Projekt mit diesem Namen existiert bereits.')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template(
                'projektverwaltung/admin/projekt_form.html',
                projekt=None,
                projekt_typen=ProjektTyp.choices(),
            )

        projekt = Projekt(
            name=name,
            beschreibung=beschreibung,
            typ=typ,
            kunde_id=int(kunde_id) if kunde_id else None
        )
        db.session.add(projekt)
        db.session.commit()

        flash(f'Projekt "{name}" wurde erstellt.', 'success')
        return redirect(url_for('projektverwaltung_admin.projekt_detail', id=projekt.id))

    return render_template(
        'projektverwaltung/admin/projekt_form.html',
        projekt=None,
        projekt_typen=ProjektTyp.choices(),
    )


@admin_bp.route('/<int:id>')
@login_required
@permission_required('admin.*')
def projekt_detail(id):
    """Show project details with Kanban board."""
    projekt = Projekt.query.get_or_404(id)

    # Sort components by last updated
    komponenten = projekt.komponenten.order_by(Komponente.updated_at.desc()).all()

    # First 3 directly, rest in dropdown
    komponenten_direkt = komponenten[:3]
    komponenten_dropdown = komponenten[3:]

    # Get active component
    aktive_komponente_id = request.args.get('komponente', type=int)
    aktive_komponente = None
    if aktive_komponente_id:
        aktive_komponente = Komponente.query.get(aktive_komponente_id)
    elif komponenten:
        aktive_komponente = komponenten[0]

    # Archive toggle query params
    show_archived_backlog = request.args.get('show_archived_backlog') == '1'
    show_archived_erledigt = request.args.get('show_archived_erledigt') == '1'

    # Task search
    suchbegriff_raw = request.args.get('q', '').strip()
    task_id_from_search = None
    if suchbegriff_raw:
        task_id_match = re.search(r'T(\d+)', suchbegriff_raw.upper())
        if task_id_match:
            task_id_from_search = int(task_id_match.group(1))

    # Get tasks for active component
    tasks_by_status = {}
    if aktive_komponente:
        for status in TaskStatus:
            query = aktive_komponente.tasks.filter_by(status=status.value)

            # Filter archived tasks
            if status.value == 'backlog' and not show_archived_backlog:
                query = query.filter_by(ist_archiviert=False)
            elif status.value == 'erledigt' and not show_archived_erledigt:
                query = query.filter_by(ist_archiviert=False)

            # Apply search
            if suchbegriff_raw:
                if task_id_from_search:
                    query = query.filter(Task.id == task_id_from_search)
                else:
                    query = query.filter(
                        db.or_(
                            Task.titel.ilike(f'%{suchbegriff_raw}%'),
                            Task.beschreibung.ilike(f'%{suchbegriff_raw}%')
                        )
                    )

            tasks_by_status[status.value] = query.order_by(Task.sortierung).all()

    # Total counts per status
    tasks_total_by_status = {}
    if aktive_komponente:
        for status in TaskStatus:
            tasks_total_by_status[status.value] = aktive_komponente.tasks.filter_by(
                status=status.value
            ).count()

    # Phase filter
    phase_filter = request.args.get('phase', '')
    phasen = TaskPhase.choices()

    # Focus mode
    fokus_modus = request.args.get('fokus') == '1'

    return render_template(
        'projektverwaltung/admin/projekt_detail.html',
        projekt=projekt,
        komponenten=komponenten,
        komponenten_direkt=komponenten_direkt,
        komponenten_dropdown=komponenten_dropdown,
        aktive_komponente=aktive_komponente,
        tasks_by_status=tasks_by_status,
        tasks_total_by_status=tasks_total_by_status,
        task_status_liste=TaskStatus,
        phase_filter=phase_filter,
        phasen=phasen,
        fokus_modus=fokus_modus,
        show_archived_backlog=show_archived_backlog,
        show_archived_erledigt=show_archived_erledigt,
        suchbegriff=suchbegriff_raw,
    )


@admin_bp.route('/<int:id>/bearbeiten', methods=['GET', 'POST'])
@login_required
@permission_required('admin.*')
def projekt_bearbeiten(id):
    """Edit a project."""
    projekt = Projekt.query.get_or_404(id)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        beschreibung = request.form.get('beschreibung', '').strip()
        typ = request.form.get('typ', ProjektTyp.INTERN.value)
        kunde_id = request.form.get('kunde_id', '').strip()
        aktiv = request.form.get('aktiv') == 'on'

        errors = []
        if not name:
            errors.append('Bitte gib einen Namen ein.')
        existing = Projekt.query.filter_by(name=name).first()
        if existing and existing.id != projekt.id:
            errors.append('Ein Projekt mit diesem Namen existiert bereits.')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template(
                'projektverwaltung/admin/projekt_form.html',
                projekt=projekt,
                projekt_typen=ProjektTyp.choices(),
            )

        projekt.name = name
        projekt.beschreibung = beschreibung
        projekt.typ = typ
        projekt.kunde_id = int(kunde_id) if kunde_id else None
        projekt.aktiv = aktiv
        db.session.commit()

        flash(f'Projekt "{name}" wurde aktualisiert.', 'success')
        return redirect(url_for('projektverwaltung_admin.projekt_detail', id=projekt.id))

    return render_template(
        'projektverwaltung/admin/projekt_form.html',
        projekt=projekt,
        projekt_typen=ProjektTyp.choices(),
    )


# =============================================================================
# KOMPONENTEN (PRDs/Modules/Entities)
# =============================================================================

@admin_bp.route('/<int:projekt_id>/komponente/neu', methods=['GET', 'POST'])
@login_required
@permission_required('admin.*')
def komponente_neu(projekt_id):
    """Create a new component."""
    projekt = Projekt.query.get_or_404(projekt_id)

    # Get available modules from V-Flask
    try:
        module = Modul.query.order_by(Modul.name).all()
    except Exception:
        module = []

    # Next PRD number
    from sqlalchemy import func
    naechste_id = db.session.query(func.max(Komponente.id)).scalar() or 0
    naechste_prd_nummer = f"{naechste_id + 1:03d}"

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        prd_nummer = request.form.get('prd_nummer', '').strip()
        typ = request.form.get('typ', KomponenteTyp.MODUL.value)
        modul_id = request.form.get('modul_id', '').strip()
        aktuelle_phase = request.form.get('aktuelle_phase', KomponentePhase.POC.value)
        icon = request.form.get('icon', 'ti-package').strip()
        prd_inhalt = request.form.get('prd_inhalt', '').strip()

        errors = []
        if not name:
            errors.append('Bitte gib einen Namen ein.')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template(
                'projektverwaltung/admin/komponente_form.html',
                projekt=projekt,
                komponente=None,
                module=module,
                komponente_typen=KomponenteTyp.choices(),
                komponente_phasen=KomponentePhase.choices(),
                naechste_prd_nummer=naechste_prd_nummer,
            )

        komponente = Komponente(
            projekt_id=projekt.id,
            name=name,
            prd_nummer=prd_nummer or None,
            typ=typ,
            modul_id=int(modul_id) if modul_id else None,
            aktuelle_phase=aktuelle_phase,
            icon=icon,
            prd_inhalt=prd_inhalt or None
        )
        db.session.add(komponente)
        db.session.commit()

        flash(f'Komponente "{name}" wurde erstellt.', 'success')
        return redirect(url_for(
            'projektverwaltung_admin.projekt_detail',
            id=projekt.id,
            komponente=komponente.id
        ))

    return render_template(
        'projektverwaltung/admin/komponente_form.html',
        projekt=projekt,
        komponente=None,
        module=module,
        komponente_typen=KomponenteTyp.choices(),
        komponente_phasen=KomponentePhase.choices(),
        naechste_prd_nummer=naechste_prd_nummer,
    )


@admin_bp.route('/komponente/<int:id>/bearbeiten', methods=['GET', 'POST'])
@login_required
@permission_required('admin.*')
def komponente_bearbeiten(id):
    """Edit a component."""
    komponente = Komponente.query.get_or_404(id)
    projekt = komponente.projekt

    try:
        module = Modul.query.order_by(Modul.name).all()
    except Exception:
        module = []

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        prd_nummer = request.form.get('prd_nummer', '').strip()
        typ = request.form.get('typ', KomponenteTyp.MODUL.value)
        modul_id = request.form.get('modul_id', '').strip()
        aktuelle_phase = request.form.get('aktuelle_phase', KomponentePhase.POC.value)
        status = request.form.get('status', KomponenteStatus.AKTIV.value)
        icon = request.form.get('icon', 'ti-package').strip()

        errors = []
        if not name:
            errors.append('Bitte gib einen Namen ein.')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template(
                'projektverwaltung/admin/komponente_form.html',
                projekt=projekt,
                komponente=komponente,
                module=module,
                komponente_typen=KomponenteTyp.choices(),
                komponente_phasen=KomponentePhase.choices(),
                komponente_status=KomponenteStatus.choices(),
            )

        komponente.name = name
        komponente.prd_nummer = prd_nummer or None
        komponente.typ = typ
        komponente.modul_id = int(modul_id) if modul_id else None
        komponente.aktuelle_phase = aktuelle_phase
        komponente.status = status
        komponente.icon = icon
        db.session.commit()

        flash(f'Komponente "{name}" wurde aktualisiert.', 'success')
        return redirect(url_for(
            'projektverwaltung_admin.projekt_detail',
            id=projekt.id,
            komponente=komponente.id
        ))

    return render_template(
        'projektverwaltung/admin/komponente_form.html',
        projekt=projekt,
        komponente=komponente,
        module=module,
        komponente_typen=KomponenteTyp.choices(),
        komponente_phasen=KomponentePhase.choices(),
        komponente_status=KomponenteStatus.choices(),
    )


@admin_bp.route('/komponente/<int:id>/prd', methods=['GET', 'POST'])
@login_required
@permission_required('admin.*')
def prd_editor(id):
    """PRD editor with Markdown preview."""
    komponente = Komponente.query.get_or_404(id)
    projekt = komponente.projekt

    if request.method == 'POST':
        prd_inhalt = request.form.get('prd_inhalt', '').strip()
        komponente.prd_inhalt = prd_inhalt
        db.session.commit()

        flash('PRD wurde gespeichert.', 'success')
        return redirect(url_for('projektverwaltung_admin.prd_editor', id=id))

    return render_template(
        'projektverwaltung/admin/prd_editor.html',
        projekt=projekt,
        komponente=komponente,
    )


# =============================================================================
# TASKS (Kanban Board)
# =============================================================================

@admin_bp.route('/komponente/<int:komponente_id>/task/neu', methods=['POST'])
@login_required
@permission_required('admin.*')
def task_neu(komponente_id):
    """Create a new task (AJAX)."""
    komponente = Komponente.query.get_or_404(komponente_id)

    titel = request.form.get('titel', '').strip()
    status = request.form.get('status', TaskStatus.BACKLOG.value)

    if not titel:
        return jsonify({'error': 'Titel ist erforderlich'}), 400

    max_sort = db.session.query(db.func.max(Task.sortierung)).filter(
        Task.komponente_id == komponente_id,
        Task.status == status
    ).scalar() or 0

    task = Task(
        komponente_id=komponente_id,
        titel=titel,
        status=status,
        phase=komponente.aktuelle_phase,
        sortierung=max_sort + 1
    )
    db.session.add(task)
    db.session.commit()

    return jsonify({
        'id': task.id,
        'task_nummer': task.task_nummer,
        'titel': task.titel,
        'status': task.status,
        'prioritaet': task.prioritaet,
        'prioritaet_badge': task.prioritaet_badge
    })


@admin_bp.route('/task/<int:id>', methods=['GET'])
@login_required
@permission_required('admin.*')
def task_detail(id):
    """Get task details (AJAX)."""
    task = Task.query.get_or_404(id)

    # Get users for assignment dropdown
    users = User.query.filter_by(aktiv=True).order_by(User.nachname, User.vorname).all()

    # Get task types from LookupWert
    try:
        task_typen = LookupWert.query.filter_by(kategorie='task_typ').all()
    except Exception:
        task_typen = []

    return render_template(
        'projektverwaltung/admin/_task_offcanvas.html',
        task=task,
        projekt=task.komponente.projekt,
        users=users,
        task_typen=task_typen,
        task_status_liste=TaskStatus.choices(),
        task_prioritaet_liste=TaskPrioritaet.choices(),
        task_phase_liste=TaskPhase.choices()
    )


@admin_bp.route('/task/<int:id>', methods=['POST'])
@login_required
@permission_required('admin.*')
def task_update(id):
    """Update a task (AJAX)."""
    task = Task.query.get_or_404(id)

    titel = request.form.get('titel', '').strip()
    beschreibung = request.form.get('beschreibung', '').strip()
    status = request.form.get('status', task.status)
    prioritaet = request.form.get('prioritaet', task.prioritaet)
    typ = request.form.get('typ', task.typ)
    phase = request.form.get('phase', task.phase)
    zugewiesen_an = request.form.get('zugewiesen_an', '').strip()

    if not titel:
        return jsonify({'error': 'Titel ist erforderlich'}), 400

    old_status = task.status
    task.titel = titel
    task.beschreibung = beschreibung or None
    task.status = status
    task.prioritaet = prioritaet
    task.typ = typ
    task.phase = phase
    task.zugewiesen_an = int(zugewiesen_an) if zugewiesen_an else None

    task.create_changelog_on_complete = request.form.get('create_changelog') == 'on'

    ist_archiviert = request.form.get('ist_archiviert') == 'on'
    if old_status != status:
        ist_archiviert = False
    task.ist_archiviert = ist_archiviert

    if status == TaskStatus.ERLEDIGT.value and old_status != TaskStatus.ERLEDIGT.value:
        task.erledigt_am = datetime.now(timezone.utc)

        if request.form.get('create_changelog') == 'on':
            changelog = ChangelogEintrag(
                komponente_id=task.komponente_id,
                task_id=task.id,
                version=task.komponente.aktuelle_phase,
                kategorie=ChangelogKategorie.ADDED.value,
                beschreibung=titel,
                erstellt_von=current_user.id
            )
            db.session.add(changelog)

    db.session.commit()

    return jsonify({
        'id': task.id,
        'titel': task.titel,
        'status': task.status,
        'prioritaet': task.prioritaet,
        'prioritaet_badge': task.prioritaet_badge,
        'erledigt': task.status == TaskStatus.ERLEDIGT.value
    })


@admin_bp.route('/task/<int:id>/delete', methods=['POST'])
@login_required
@permission_required('admin.*')
def task_delete(id):
    """Delete a task (AJAX)."""
    task = Task.query.get_or_404(id)

    db.session.delete(task)
    db.session.commit()

    return jsonify({'success': True})


@admin_bp.route('/tasks/reorder', methods=['POST'])
@login_required
@permission_required('admin.*')
def tasks_reorder():
    """Reorder tasks via drag & drop (AJAX)."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid data'}), 400

    task_id = data.get('task_id')
    new_status = data.get('status')
    order = data.get('order', [])

    if task_id and new_status:
        task = Task.query.get(task_id)
        if task:
            if task.status != new_status:
                task.ist_archiviert = False
            task.status = new_status
            db.session.commit()

    for idx, tid in enumerate(order):
        task = Task.query.get(tid)
        if task:
            task.sortierung = idx
    db.session.commit()

    return jsonify({'success': True})


# =============================================================================
# CHANGELOG
# =============================================================================

@admin_bp.route('/komponente/<int:id>/changelog')
@login_required
@permission_required('admin.*')
def changelog_liste(id):
    """Show changelog for a component."""
    komponente = Komponente.query.get_or_404(id)
    projekt = komponente.projekt

    eintraege = komponente.changelog_eintraege.order_by(
        ChangelogEintrag.erstellt_am.desc()
    ).all()

    return render_template(
        'projektverwaltung/admin/changelog.html',
        projekt=projekt,
        komponente=komponente,
        eintraege=eintraege,
        kategorien=ChangelogKategorie.choices(),
    )


@admin_bp.route('/komponente/<int:komponente_id>/changelog/neu', methods=['POST'])
@login_required
@permission_required('admin.*')
def changelog_neu(komponente_id):
    """Create a new changelog entry."""
    komponente = Komponente.query.get_or_404(komponente_id)

    version = request.form.get('version', '').strip()
    kategorie = request.form.get('kategorie', ChangelogKategorie.ADDED.value)
    beschreibung = request.form.get('beschreibung', '').strip()
    sichtbarkeit = request.form.get('sichtbarkeit', ChangelogSichtbarkeit.INTERN.value)

    if not beschreibung:
        flash('Bitte gib eine Beschreibung ein.', 'error')
        return redirect(url_for('projektverwaltung_admin.changelog_liste', id=komponente_id))

    eintrag = ChangelogEintrag(
        komponente_id=komponente_id,
        version=version or komponente.aktuelle_phase,
        kategorie=kategorie,
        beschreibung=beschreibung,
        sichtbarkeit=sichtbarkeit,
        erstellt_von=current_user.id
    )
    db.session.add(eintrag)
    db.session.commit()

    flash('Changelog-Eintrag wurde erstellt.', 'success')
    return redirect(url_for('projektverwaltung_admin.changelog_liste', id=komponente_id))


# =============================================================================
# EINSTELLUNGEN (Settings)
# =============================================================================

@admin_bp.route('/einstellungen', methods=['GET', 'POST'])
@login_required
@permission_required('admin.*')
def einstellungen():
    """Projektverwaltung settings page."""
    if request.method == 'POST':
        suffix = request.form.get('ki_prompt_suffix', '')

        try:
            config = Config.query.filter_by(key='projektverwaltung_ki_prompt_suffix').first()
            if config:
                config.value = suffix
            else:
                config = Config(
                    key='projektverwaltung_ki_prompt_suffix',
                    value=suffix,
                    beschreibung='KI-Prompt Suffix für Projektverwaltung Tasks'
                )
                db.session.add(config)
            db.session.commit()
            flash('Einstellungen gespeichert.', 'success')
        except Exception as e:
            flash(f'Fehler beim Speichern: {e}', 'error')

        return redirect(url_for('projektverwaltung_admin.einstellungen'))

    try:
        config = Config.query.filter_by(key='projektverwaltung_ki_prompt_suffix').first()
        ki_prompt_suffix = config.value if config else ''
    except Exception:
        ki_prompt_suffix = ''

    return render_template(
        'projektverwaltung/admin/einstellungen.html',
        ki_prompt_suffix=ki_prompt_suffix
    )
