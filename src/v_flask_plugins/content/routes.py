"""Admin routes for the Content plugin."""
from flask import (
    Blueprint,
    render_template,
    request,
    flash,
    redirect,
    url_for,
    jsonify,
)
from v_flask import db
from v_flask.auth import permission_required

# Admin Blueprint
content_admin_bp = Blueprint(
    'content_admin',
    __name__,
    template_folder='templates'
)


# === List & Overview ===

@content_admin_bp.route('/')
@permission_required('admin.*')
def list_blocks():
    """List all content blocks."""
    from v_flask_plugins.content.models import ContentBlock

    blocks = (
        ContentBlock.query
        .order_by(ContentBlock.created_at.desc())
        .all()
    )

    return render_template(
        'content/admin/list.html',
        blocks=blocks
    )


# === Create Wizard: Step 1 - Choose Intention ===

@content_admin_bp.route('/neu')
@permission_required('admin.*')
def create_step1():
    """Step 1: Choose intention for new content block."""
    from v_flask_plugins.content.services.content_service import content_service

    intentions = content_service.get_intentions()

    return render_template(
        'content/admin/create_step1.html',
        intentions=intentions
    )


# === Create Wizard: Step 2 - Choose Layout ===

@content_admin_bp.route('/neu/<intention>')
@permission_required('admin.*')
def create_step2(intention: str):
    """Step 2: Choose layout for the content block."""
    from v_flask_plugins.content.services.content_service import content_service

    intention_data = content_service.get_intention_by_id(intention)
    if not intention_data:
        flash('Ungültige Intention ausgewählt.', 'error')
        return redirect(url_for('content_admin.create_step1'))

    layouts = content_service.get_layouts_for_intention(intention)

    return render_template(
        'content/admin/create_step2.html',
        intention=intention_data,
        layouts=layouts
    )


# === Create Wizard: Step 3 - Fill Content ===

@content_admin_bp.route('/neu/<intention>/<layout>')
@permission_required('admin.*')
def create_step3(intention: str, layout: str):
    """Step 3: Fill in content for the block."""
    from v_flask_plugins.content.services.content_service import content_service
    from v_flask_plugins.content.services.snippet_service import snippet_service

    intention_data = content_service.get_intention_by_id(intention)
    layout_data = content_service.get_layout_by_id(layout)

    if not intention_data or not layout_data:
        flash('Ungültige Auswahl.', 'error')
        return redirect(url_for('content_admin.create_step1'))

    # Get snippets for the intention category
    # Map intention to kategorie for snippets
    kategorie_map = {
        'ueber_uns': 'ueber_uns',
        'leistungen': 'leistungen',
        'team': 'team',
        'frei': None,  # Show all for free content
    }
    kategorie = kategorie_map.get(intention)
    snippets = snippet_service.get_all_snippets(kategorie=kategorie)

    return render_template(
        'content/admin/create_step3.html',
        intention=intention_data,
        layout=layout_data,
        snippets=snippets
    )


# === Save New Content Block ===

@content_admin_bp.route('/speichern', methods=['POST'])
@permission_required('admin.*')
def save_block():
    """Save a new or updated content block."""
    from v_flask_plugins.content.models import ContentBlock

    block_id = request.form.get('block_id')
    name = request.form.get('name', '').strip()
    intention = request.form.get('intention', '').strip()
    layout = request.form.get('layout', '').strip()
    titel = request.form.get('titel', '').strip()
    text = request.form.get('text', '').strip()
    bild_id = request.form.get('bild_id')

    if not name:
        flash('Bitte gib einen Namen für den Baustein ein.', 'error')
        return redirect(request.referrer or url_for('content_admin.list_blocks'))

    # Build content_data
    content_data = {
        'titel': titel,
        'text': text,
        'bilder': [],
    }

    if bild_id:
        # Store media reference
        content_data['bilder'].append({
            'media_id': int(bild_id),
            'position': 0
        })

    if block_id:
        # Update existing
        block = ContentBlock.query.get_or_404(int(block_id))
        block.name = name
        block.intention = intention
        block.layout = layout
        block.content_data = content_data
        flash('Inhaltsbaustein aktualisiert.', 'success')
    else:
        # Create new
        block = ContentBlock(
            name=name,
            intention=intention,
            layout=layout,
            content_data=content_data,
            active=True
        )
        db.session.add(block)
        flash('Inhaltsbaustein erstellt.', 'success')

    db.session.commit()

    return redirect(url_for('content_admin.list_blocks'))


# === Edit Existing Block ===

@content_admin_bp.route('/<int:block_id>/bearbeiten')
@permission_required('admin.*')
def edit_block(block_id: int):
    """Edit an existing content block."""
    from v_flask_plugins.content.models import ContentBlock
    from v_flask_plugins.content.services.content_service import content_service
    from v_flask_plugins.content.services.snippet_service import snippet_service

    block = ContentBlock.query.get_or_404(block_id)

    intention_data = content_service.get_intention_by_id(block.intention)
    layout_data = content_service.get_layout_by_id(block.layout)
    layouts = content_service.get_layouts_for_intention(block.intention)
    snippets = snippet_service.get_all_snippets()

    return render_template(
        'content/admin/edit.html',
        block=block,
        intention=intention_data,
        layout=layout_data,
        layouts=layouts,
        snippets=snippets
    )


# === Toggle Active Status ===

@content_admin_bp.route('/<int:block_id>/toggle', methods=['POST'])
@permission_required('admin.*')
def toggle_block(block_id: int):
    """Toggle active status of a content block."""
    from v_flask_plugins.content.models import ContentBlock

    block = ContentBlock.query.get_or_404(block_id)
    block.active = not block.active
    db.session.commit()

    status = 'aktiviert' if block.active else 'deaktiviert'
    flash(f'Baustein "{block.name}" {status}.', 'success')

    return redirect(url_for('content_admin.list_blocks'))


# === Delete Block ===

@content_admin_bp.route('/<int:block_id>/loeschen', methods=['POST'])
@permission_required('admin.*')
def delete_block(block_id: int):
    """Delete a content block."""
    from v_flask_plugins.content.models import ContentBlock

    block = ContentBlock.query.get_or_404(block_id)
    name = block.name

    db.session.delete(block)
    db.session.commit()

    flash(f'Baustein "{name}" gelöscht.', 'success')

    return redirect(url_for('content_admin.list_blocks'))


# === Assignment Management ===

@content_admin_bp.route('/<int:block_id>/zuweisen')
@permission_required('admin.*')
def assign_block(block_id: int):
    """Manage page assignments for a content block."""
    from v_flask_plugins.content.models import ContentBlock, ContentAssignment
    from v_flask.content_slots.models import PageRoute

    block = ContentBlock.query.get_or_404(block_id)

    # Get all assignable page routes
    page_routes = (
        PageRoute.query
        .filter_by(hero_assignable=True)
        .filter(PageRoute.route_type == 'page')
        .order_by(PageRoute.display_name)
        .all()
    )

    # Get existing assignments
    assignments = {
        a.page_route_id: a
        for a in block.assignments
    }

    return render_template(
        'content/admin/assign.html',
        block=block,
        page_routes=page_routes,
        assignments=assignments
    )


@content_admin_bp.route('/<int:block_id>/zuweisen/speichern', methods=['POST'])
@permission_required('admin.*')
def save_assignments(block_id: int):
    """Save page assignments for a content block."""
    from v_flask_plugins.content.models import ContentBlock, ContentAssignment

    block = ContentBlock.query.get_or_404(block_id)

    # Get selected page IDs from form
    selected_pages = request.form.getlist('pages')
    slot_position = request.form.get('slot_position', 'after_content')

    # Remove existing assignments
    ContentAssignment.query.filter_by(content_block_id=block_id).delete()

    # Create new assignments
    for i, page_id in enumerate(selected_pages):
        assignment = ContentAssignment(
            content_block_id=block_id,
            page_route_id=int(page_id),
            slot_position=slot_position,
            sort_order=i,
            active=True
        )
        db.session.add(assignment)

    db.session.commit()

    flash(f'Seitenzuweisungen für "{block.name}" gespeichert.', 'success')

    return redirect(url_for('content_admin.list_blocks'))


# === Snippets Management ===

@content_admin_bp.route('/textbausteine')
@permission_required('admin.*')
def list_snippets():
    """List all text snippets."""
    from v_flask_plugins.content.models import TextSnippet
    from v_flask_plugins.content.services.snippet_service import snippet_service

    # Get user-created snippets from DB
    db_snippets = TextSnippet.query.order_by(TextSnippet.kategorie, TextSnippet.name).all()

    # Get system snippets from files
    system_snippets = snippet_service.get_system_snippets()

    categories = snippet_service.get_available_categories()

    return render_template(
        'content/admin/snippets_list.html',
        db_snippets=db_snippets,
        system_snippets=system_snippets,
        categories=categories
    )


@content_admin_bp.route('/textbausteine/neu', methods=['GET', 'POST'])
@permission_required('admin.*')
def create_snippet():
    """Create a new text snippet."""
    from v_flask_plugins.content.services.snippet_service import snippet_service

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        kategorie = request.form.get('kategorie', '').strip()
        titel = request.form.get('titel', '').strip()
        text = request.form.get('text', '').strip()

        if not name or not kategorie:
            flash('Name und Kategorie sind Pflichtfelder.', 'error')
        else:
            snippet_service.create_snippet(
                name=name,
                kategorie=kategorie,
                titel=titel,
                text=text
            )
            flash('Textbaustein erstellt.', 'success')
            return redirect(url_for('content_admin.list_snippets'))

    categories = snippet_service.get_available_categories()

    return render_template(
        'content/admin/snippet_edit.html',
        snippet=None,
        categories=categories
    )


# === API Endpoints ===

@content_admin_bp.route('/api/snippets')
@permission_required('admin.*')
def api_snippets():
    """API endpoint to get snippets by category."""
    from v_flask_plugins.content.services.snippet_service import snippet_service

    kategorie = request.args.get('kategorie')
    branche = request.args.get('branche')

    snippets = snippet_service.get_all_snippets(
        kategorie=kategorie,
        branche=branche
    )

    return jsonify(snippets)


@content_admin_bp.route('/api/layouts/<intention>')
@permission_required('admin.*')
def api_layouts(intention: str):
    """API endpoint to get layouts for an intention."""
    from v_flask_plugins.content.services.content_service import content_service

    layouts = content_service.get_layouts_for_intention(intention)

    return jsonify(layouts)
