/**
 * Tabler Icon Picker (DaisyUI Version)
 *
 * Central icon picker for selecting Tabler Icons.
 * Displayed as a DaisyUI drawer that can be opened from modals.
 */

// State
let iconPickerTargetInput = null;
let tablerIcons = [];
let iconsLoaded = false;

/**
 * Opens the icon picker for a specific input field
 * @param {string} inputId - The ID of the target input field
 */
async function openIconPicker(inputId) {
    iconPickerTargetInput = document.getElementById(inputId);

    if (!iconPickerTargetInput) {
        console.error('Icon Picker: Input not found:', inputId);
        return;
    }

    // Find the drawer toggle checkbox
    const drawerToggle = document.getElementById('iconPickerToggle');
    if (!drawerToggle) {
        console.error('Icon Picker: Drawer toggle not found');
        return;
    }

    // Load icons if not already done
    if (!iconsLoaded) {
        await loadTablerIcons();
    }

    // Pre-select current value
    const currentValue = iconPickerTargetInput.value;
    highlightSelectedIcon(currentValue);

    // Clear search field
    const searchInput = document.getElementById('iconSearchInput');
    if (searchInput) {
        searchInput.value = '';
    }

    // Show all icons
    renderIcons(tablerIcons);

    // Open drawer by checking the toggle
    drawerToggle.checked = true;

    // Focus search field after a short delay
    setTimeout(() => {
        searchInput?.focus();
    }, 100);
}

/**
 * Closes the icon picker drawer
 */
function closeIconPicker() {
    const drawerToggle = document.getElementById('iconPickerToggle');
    if (drawerToggle) {
        drawerToggle.checked = false;
    }
}

/**
 * Loads the Tabler Icons list
 */
async function loadTablerIcons() {
    const statusEl = document.getElementById('iconLoadingStatus');

    try {
        if (statusEl) statusEl.textContent = 'Lade Icons...';

        // Use v_flask_static blueprint URL
        const response = await fetch('/v_flask_static/js/tabler-icons-list.json');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        tablerIcons = await response.json();
        iconsLoaded = true;

        if (statusEl) statusEl.textContent = '';
        updateIconCount(tablerIcons.length);

        console.log(`Icon Picker: ${tablerIcons.length} icons loaded`);

    } catch (error) {
        console.error('Icon Picker: Error loading icons:', error);
        if (statusEl) statusEl.textContent = 'Fehler beim Laden';

        // Fallback: minimal icon list
        tablerIcons = [
            {name: 'ti-home', tags: ['house', 'building', 'main']},
            {name: 'ti-user', tags: ['person', 'account', 'profile']},
            {name: 'ti-settings', tags: ['config', 'gear', 'preferences']},
            {name: 'ti-search', tags: ['find', 'magnifying', 'glass']},
            {name: 'ti-plus', tags: ['add', 'new', 'create']},
            {name: 'ti-edit', tags: ['pencil', 'modify', 'change']},
            {name: 'ti-trash', tags: ['delete', 'remove', 'bin']},
            {name: 'ti-check', tags: ['done', 'complete', 'success']},
            {name: 'ti-x', tags: ['close', 'cancel', 'remove']},
            {name: 'ti-alert-triangle', tags: ['warning', 'danger', 'error']},
            {name: 'ti-player-play', tags: ['start', 'video', 'music', 'begin']}
        ];
        iconsLoaded = true;
        updateIconCount(tablerIcons.length);
    }

    renderIcons(tablerIcons);
}

/**
 * Renders the icon list in the grid
 * @param {Object[]} icons - Array of icon objects {name, tags}
 */
function renderIcons(icons) {
    const grid = document.getElementById('iconGrid');
    if (!grid) return;

    if (icons.length === 0) {
        grid.innerHTML = `
            <div class="text-center text-base-content/50 py-4 col-span-full">
                <i class="ti ti-mood-sad text-4xl"></i>
                <p class="mt-2 mb-0">Keine Icons gefunden</p>
            </div>
        `;
        return;
    }

    // Performance: use DocumentFragment
    const fragment = document.createDocumentFragment();

    icons.forEach(iconData => {
        // Support both old format (string) and new format (object)
        const iconName = typeof iconData === 'string' ? iconData : iconData.name;

        const item = document.createElement('button');
        item.type = 'button';
        item.className = 'icon-grid-item btn btn-ghost btn-sm aspect-square';
        item.title = iconName;
        item.onclick = () => selectIcon(iconName);

        const icon = document.createElement('i');
        icon.className = `ti ${iconName} text-xl`;
        item.appendChild(icon);

        fragment.appendChild(item);
    });

    grid.innerHTML = '';
    grid.appendChild(fragment);

    updateIconCount(icons.length);
}

/**
 * Filters icons by search term (searches name AND tags)
 * @param {string} query - Search term
 */
function filterIcons(query) {
    const searchTerm = query.toLowerCase().trim();

    if (!searchTerm) {
        renderIcons(tablerIcons);
        return;
    }

    const filtered = tablerIcons.filter(iconData => {
        // Support both old format (string) and new format (object)
        if (typeof iconData === 'string') {
            const name = iconData.replace('ti-', '');
            return name.includes(searchTerm);
        }

        // New format with tags
        // 1. Search in icon name (without 'ti-' prefix)
        const name = iconData.name.replace('ti-', '');
        if (name.includes(searchTerm)) {
            return true;
        }

        // 2. Search in tags
        if (iconData.tags && Array.isArray(iconData.tags)) {
            return iconData.tags.some(tag =>
                tag.toLowerCase().includes(searchTerm)
            );
        }

        return false;
    });

    renderIcons(filtered);
}

/**
 * Clears the search field and shows all icons
 */
function clearIconSearch() {
    const searchInput = document.getElementById('iconSearchInput');
    if (searchInput) {
        searchInput.value = '';
        searchInput.focus();
    }
    renderIcons(tablerIcons);
}

/**
 * Selects an icon and transfers it to the target input
 * @param {string} iconName - The selected icon name (always with ti- prefix)
 */
function selectIcon(iconName) {
    if (!iconPickerTargetInput) {
        console.error('Icon Picker: No target input defined');
        return;
    }

    // Check if the field expects icons without prefix
    const stripPrefix = iconPickerTargetInput.dataset.stripPrefix === 'true';
    let valueToSet = iconName;

    if (stripPrefix && iconName.startsWith('ti-')) {
        valueToSet = iconName.substring(3); // Remove 'ti-' prefix
    }

    // Write value to input field
    iconPickerTargetInput.value = valueToSet;

    // Update preview
    updateIconPreviewFor(iconPickerTargetInput.id);

    // Trigger change event (for other event handlers)
    iconPickerTargetInput.dispatchEvent(new Event('change', { bubbles: true }));

    // Close drawer
    closeIconPicker();
}

/**
 * Updates the icon preview for an input field
 * @param {string} inputId - The ID of the input field
 */
function updateIconPreviewFor(inputId) {
    const input = document.getElementById(inputId);
    const preview = document.getElementById(`preview-${inputId}`);

    if (!input || !preview) return;

    let iconName = input.value.trim();

    if (iconName) {
        // Normalize: add ti- prefix if not present
        if (!iconName.startsWith('ti-')) {
            iconName = 'ti-' + iconName;
        }
        preview.innerHTML = `<i class="ti ${iconName}"></i>`;
    } else {
        // Fallback icon
        preview.innerHTML = '<i class="ti ti-icons"></i>';
    }
}

/**
 * Highlights the currently selected icon in the grid
 * @param {string} iconName - The icon name (with or without ti- prefix)
 */
function highlightSelectedIcon(iconName) {
    // Remove all highlights
    document.querySelectorAll('.icon-grid-item.btn-primary').forEach(el => {
        el.classList.remove('btn-primary');
        el.classList.add('btn-ghost');
    });

    if (!iconName) return;

    // Normalize: add ti- prefix if not present
    let normalizedName = iconName;
    if (!normalizedName.startsWith('ti-')) {
        normalizedName = 'ti-' + normalizedName;
    }

    // Highlight new icon
    const grid = document.getElementById('iconGrid');
    if (!grid) return;

    const items = grid.querySelectorAll('.icon-grid-item');
    items.forEach(item => {
        if (item.title === normalizedName) {
            item.classList.remove('btn-ghost');
            item.classList.add('btn-primary');
            // Scroll into view
            item.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    });
}

/**
 * Updates the icon count display
 * @param {number} count - Number of icons
 */
function updateIconCount(count) {
    const countEl = document.getElementById('iconCount');
    if (countEl) {
        countEl.textContent = count.toLocaleString('de-DE');
    }
}

// Keyboard support for search
document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('iconSearchInput');
    if (searchInput) {
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                closeIconPicker();
            }
        });
    }
});
