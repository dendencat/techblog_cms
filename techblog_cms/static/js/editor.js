/*
 * Distraction-free article editor.
 *
 * - Write / split / preview modes; the preview uses the same server renderer and CSS as the
 *   public page. Auto-growing title and body, sticky toolbar, smart list continuation.
 * - Tag chips with suggestions, settings drawer, cover image, Ghost-style publish dialog.
 * - Ctrl+S save, local autosave with restore, unsaved-changes guard.
 * - Instant image upload from picker, drag & drop, or paste.
 * Configuration comes from window.EDITOR_CONFIG (set in article_editor.html).
 */
(() => {
    'use strict';

    const config = window.EDITOR_CONFIG || {};
    const form = document.getElementById('articleForm');
    const textarea = document.getElementById('content');
    const titleInput = document.getElementById('title');
    const preview = document.getElementById('preview');
    if (!form || !textarea || !preview) {
        return;
    }

    const $ = (selector, root = document) => root.querySelector(selector);
    const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));
    const csrfToken = () => ($('[name=csrfmiddlewaretoken]', form) || {}).value || '';
    const isMac = /Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent);
    const timeFormat = new Intl.DateTimeFormat('ja-JP', { hour: '2-digit', minute: '2-digit' });
    const body = $('#editor-body');
    const writeScroller = $('.ed-write');
    const saveStatus = $('#save-status');

    function debounce(fn, delay) {
        let timer = null;
        return (...args) => {
            clearTimeout(timer);
            timer = setTimeout(() => fn(...args), delay);
        };
    }

    function setStatus(text, { dirty = false } = {}) {
        if (!saveStatus) {
            return;
        }
        saveStatus.textContent = text;
        saveStatus.classList.toggle('is-dirty', dirty);
    }

    function toast(message, { error = false } = {}) {
        const stack = $('.ed-toast-stack');
        if (!stack) {
            return;
        }
        const item = document.createElement('div');
        item.className = `ed-toast${error ? ' is-error' : ''}`;
        item.textContent = message;
        stack.appendChild(item);
        setTimeout(() => item.remove(), error ? 6000 : 3500);
    }
    $$('[data-toast]').forEach((item) => setTimeout(() => item.remove(), 3500));

    // ------------------------------------------------------------------
    // Auto-growing fields (keep the scroll position steady while resizing)
    // ------------------------------------------------------------------
    function scroller() {
        return body.dataset.mode === 'split' && window.matchMedia('(min-width: 1024px)').matches ? writeScroller : null;
    }

    function grow(field) {
        if (!field) {
            return;
        }
        const container = scroller();
        const top = container ? container.scrollTop : window.scrollY;
        field.style.height = 'auto';
        field.style.height = `${field.scrollHeight}px`;
        if (container) {
            container.scrollTop = top;
        } else {
            window.scrollTo(window.scrollX, top);
        }
    }

    // ------------------------------------------------------------------
    // Text editing helpers (execCommand keeps the browser's undo stack)
    // ------------------------------------------------------------------
    function replaceSelection(text, selectStart = null, selectEnd = null) {
        const start = textarea.selectionStart;
        textarea.focus();
        let inserted = false;
        try {
            inserted = document.execCommand('insertText', false, text);
        } catch (error) {
            inserted = false;
        }
        if (!inserted) {
            textarea.setRangeText(text, textarea.selectionStart, textarea.selectionEnd, 'end');
            textarea.dispatchEvent(new Event('input', { bubbles: true }));
        }
        if (selectStart !== null) {
            textarea.setSelectionRange(start + selectStart, start + (selectEnd ?? selectStart));
        }
    }

    function selectedText() {
        return textarea.value.substring(textarea.selectionStart, textarea.selectionEnd);
    }

    function wrap(before, after, placeholder) {
        const text = selectedText() || placeholder;
        replaceSelection(before + text + after, before.length, before.length + text.length);
    }

    /** Expand the selection to whole lines, drop any prefix matching `strip`, then prefix each line. */
    function prefixLines(makePrefix, strip) {
        const value = textarea.value;
        const lineStart = value.lastIndexOf('\n', textarea.selectionStart - 1) + 1;
        let end = textarea.selectionEnd;
        if (end > textarea.selectionStart && value[end - 1] === '\n') {
            end -= 1;
        }
        let lineEnd = value.indexOf('\n', end);
        if (lineEnd === -1) {
            lineEnd = value.length;
        }
        textarea.setSelectionRange(lineStart, lineEnd);
        const lines = value.substring(lineStart, lineEnd).split('\n');
        const result = lines.map((line, index) => makePrefix(index) + (strip ? line.replace(strip, '') : line)).join('\n');
        replaceSelection(result, result.length);
    }

    /** Insert a block on its own lines, separated from surrounding text by blank lines. */
    function insertBlock(block, cursorOffset = null) {
        const value = textarea.value;
        const before = value.substring(0, textarea.selectionStart);
        const after = value.substring(textarea.selectionEnd);
        const lead = before === '' || before.endsWith('\n\n') ? '' : (before.endsWith('\n') ? '\n' : '\n\n');
        const trail = after.startsWith('\n\n') ? '' : (after.startsWith('\n') ? '\n' : '\n\n');
        const text = lead + block + trail;
        const caret = cursorOffset === null ? lead.length + block.length + trail.length : lead.length + cursorOffset;
        replaceSelection(text, caret);
    }

    const HEADING_PREFIX = /^#{1,6} /;
    const LIST_PREFIX = /^([-*+]|\d+\.) /;

    const formatters = {
        h2: () => prefixLines(() => '## ', HEADING_PREFIX),
        h3: () => prefixLines(() => '### ', HEADING_PREFIX),
        bold: () => wrap('**', '**', '太字'),
        italic: () => wrap('*', '*', '斜体'),
        code: () => wrap('`', '`', 'code'),
        link: () => {
            const text = selectedText();
            if (/^https?:\/\//.test(text)) {
                replaceSelection(`[リンクテキスト](${text})`, 1, 8);
            } else {
                const label = text || 'リンクテキスト';
                replaceSelection(`[${label}](https://)`, label.length + 3, label.length + 11);
            }
        },
        ul: () => prefixLines(() => '- ', LIST_PREFIX),
        ol: () => prefixLines((index) => `${index + 1}. `, LIST_PREFIX),
        quote: () => prefixLines(() => '> '),
        codeblock: () => {
            const code = selectedText();
            const language = window.prompt('言語名（例: python, bash, yaml。空欄可）', '');
            if (language === null) {
                return;
            }
            const lang = language.trim();
            insertBlock('```' + lang + '\n' + code + '\n```', 4 + lang.length);
        },
        table: () => insertBlock('| 見出し1 | 見出し2 |\n| --- | --- |\n| 内容 | 内容 |', 2),
        hr: () => insertBlock('---'),
        image: () => imagePicker && imagePicker.click(),
    };

    $$('[data-format]').forEach((button) => {
        button.addEventListener('click', (event) => {
            event.preventDefault();
            const formatter = formatters[button.dataset.format];
            if (formatter) {
                formatter();
            }
        });
    });

    // Enter on a list / quote line continues it; Enter on an empty item ends the list.
    textarea.addEventListener('keydown', (event) => {
        if (event.key !== 'Enter' || event.isComposing || event.shiftKey || event.ctrlKey || event.metaKey || event.altKey) {
            return;
        }
        if (textarea.selectionStart !== textarea.selectionEnd) {
            return;
        }
        const value = textarea.value;
        const caret = textarea.selectionStart;
        const lineStart = value.lastIndexOf('\n', caret - 1) + 1;
        const line = value.substring(lineStart, caret);
        const match = line.match(/^(\s*)([-*+] |(\d+)\. |> )(.*)$/);
        if (!match) {
            return;
        }
        const [, indent, marker, number, text] = match;
        event.preventDefault();
        if (!text.trim()) {
            // Empty item: drop just the marker, leaving an empty line (ends the list).
            textarea.setSelectionRange(lineStart, caret);
            let deleted = false;
            try {
                deleted = document.execCommand('delete');
            } catch (error) {
                deleted = false;
            }
            if (!deleted) {
                textarea.setRangeText('', lineStart, caret, 'end');
                textarea.dispatchEvent(new Event('input', { bubbles: true }));
            }
            return;
        }
        const next = number ? `${parseInt(number, 10) + 1}. ` : marker;
        replaceSelection(`\n${indent}${next}`);
    });

    // ------------------------------------------------------------------
    // Dialogs, drawer, tabs
    // ------------------------------------------------------------------
    const helpDialog = $('#help-dialog');
    const publishDialog = $('#publish-dialog');
    $$('dialog [data-close-dialog]').forEach((button) => {
        button.addEventListener('click', () => button.closest('dialog').close());
    });
    $$('dialog').forEach((dialog) => {
        dialog.addEventListener('click', (event) => {
            if (event.target === dialog) {
                dialog.close();
            }
        });
    });
    function openHelp() {
        if (helpDialog && typeof helpDialog.showModal === 'function' && !helpDialog.open) {
            helpDialog.showModal();
        }
    }
    $$('[data-open-help]').forEach((button) => button.addEventListener('click', openHelp));

    const drawer = $('#settings-drawer');
    const drawerBackdrop = $('[data-drawer-backdrop]');
    const drawerToggles = $$('[data-open-drawer]');
    function setDrawer(open, tab) {
        drawer.classList.toggle('is-open', open);
        drawerBackdrop.classList.toggle('hidden', !open);
        drawerToggles.forEach((button) => button.setAttribute('aria-expanded', String(open)));
        if (tab) {
            selectTab(tab);
        }
        if (open) {
            const firstField = $('[role=tabpanel]:not([hidden]) input, [role=tabpanel]:not([hidden]) select, [role=tabpanel]:not([hidden]) label', drawer);
            setTimeout(() => (firstField || drawer).focus({ preventScroll: true }), 50);
        }
    }
    drawerToggles.forEach((button) => button.addEventListener('click', () => setDrawer(!drawer.classList.contains('is-open'))));
    $$('[data-close-drawer]').forEach((button) => button.addEventListener('click', () => setDrawer(false)));
    drawerBackdrop.addEventListener('click', () => setDrawer(false));
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && drawer.classList.contains('is-open') && !$('dialog[open]')) {
            setDrawer(false);
            if (drawerToggles[0]) {
                drawerToggles[0].focus();
            }
        }
    });

    const tabs = $$('[role=tab]', drawer);
    function selectTab(tabId) {
        tabs.forEach((tab) => {
            const selected = tab.id === tabId;
            tab.setAttribute('aria-selected', String(selected));
            tab.tabIndex = selected ? 0 : -1;
            document.getElementById(tab.getAttribute('aria-controls')).hidden = !selected;
        });
    }
    tabs.forEach((tab, index) => {
        tab.addEventListener('click', () => selectTab(tab.id));
        tab.addEventListener('keydown', (event) => {
            if (event.key === 'ArrowRight' || event.key === 'ArrowLeft') {
                const next = tabs[(index + (event.key === 'ArrowRight' ? 1 : tabs.length - 1)) % tabs.length];
                selectTab(next.id);
                next.focus();
            }
        });
    });
    if (drawer.hasAttribute('data-open-on-load')) {
        setDrawer(true);
    }

    // ------------------------------------------------------------------
    // Saving: Ctrl+S, confirmations, unsaved-changes guard
    // ------------------------------------------------------------------
    const defaultSubmit = $('[data-default-submit]', form);
    let dirty = false;
    let submitting = false;

    document.addEventListener('keydown', (event) => {
        const mod = isMac ? event.metaKey : event.ctrlKey;
        if (!mod || event.altKey) {
            return;
        }
        if (event.key.toLowerCase() === 's') {
            event.preventDefault();
            if (defaultSubmit) {
                form.requestSubmit(defaultSubmit);
            }
        } else if (event.key === '/') {
            event.preventDefault();
            openHelp();
        } else if (event.shiftKey && event.code === 'KeyP') {
            event.preventDefault();
            setMode(body.dataset.mode === 'preview' ? 'write' : 'preview');
        }
    });

    textarea.addEventListener('keydown', (event) => {
        const mod = isMac ? event.metaKey : event.ctrlKey;
        if (!mod || event.altKey) {
            return;
        }
        // event.code keeps Shift+digit shortcuts working on JIS and US layouts alike.
        const shortcuts = event.shiftKey
            ? { KeyK: 'codeblock', Digit7: 'ol', Digit8: 'ul' }
            : { KeyB: 'bold', KeyI: 'italic', KeyK: 'link' };
        const format = shortcuts[event.code];
        if (format) {
            event.preventDefault();
            formatters[format]();
        }
    });

    $$('[data-confirm]', form).forEach((button) => {
        button.addEventListener('click', (event) => {
            if (!window.confirm(button.dataset.confirm)) {
                event.preventDefault();
            }
        });
    });

    form.addEventListener('input', (event) => {
        if (!event.target.closest('dialog')) {
            dirty = true;
        }
    });
    form.addEventListener('submit', () => {
        submitting = true;
        try {
            sessionStorage.setItem('techblog:editor:submitted', config.storageKey);
        } catch (error) { /* storage unavailable */ }
        $$('button[type=submit]', form).forEach((button) => {
            // Disable after the browser has captured the clicked button's name/value.
            setTimeout(() => { button.disabled = true; }, 0);
        });
        setStatus('保存しています…');
    });
    window.addEventListener('beforeunload', (event) => {
        if (dirty && !submitting) {
            event.preventDefault();
            event.returnValue = '';
        }
    });

    // ------------------------------------------------------------------
    // Publish dialog (Ghost-style: choose now / schedule, pre-flight checklist)
    // ------------------------------------------------------------------
    const publishButton = $('[data-publish-flow]');
    const publishedAtField = $('#published_at');
    const excerptField = $('#excerpt');
    const tagsField = $('#tags');
    let tagEntry = null;
    let renderTags = () => {};

    function toLocalInputValue(date) {
        const pad = (number) => String(number).padStart(2, '0');
        return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
    }

    function buildChecklist() {
        const list = $('[data-publish-checklist]', publishDialog);
        list.innerHTML = '';
        const tagCount = (tagsField.value || '').split(',').map((name) => name.trim()).filter(Boolean).length;
        const chars = textarea.value.replace(/\s/g, '').length;
        const items = [
            { ok: titleInput.value.trim().length > 0, okText: 'タイトル', ngText: 'タイトルが空です', blocking: true },
            { ok: chars > 0, okText: `本文 ${chars.toLocaleString('ja-JP')} 文字`, ngText: '本文が空です', blocking: true },
            { ok: tagCount > 0, okText: `タグ ${tagCount} 個`, ngText: 'タグがありません（見つけてもらいやすくなります）', action: () => tagEntry && tagEntry.focus() },
            { ok: excerptField.value.trim().length > 0, okText: '抜粋あり', ngText: '抜粋は本文の冒頭から自動生成されます', action: () => { setDrawer(true, 'tab-settings'); excerptField.focus(); } },
            { ok: !$('[data-cover]').classList.contains('hidden'), okText: 'カバー画像あり', ngText: 'カバー画像なし（SNS のシェア画像になります）', action: () => $('#cover_image').click() },
        ];
        let blocked = false;
        items.forEach((item) => {
            const li = document.createElement('li');
            li.className = `ed-check ${item.ok ? 'is-ok' : 'is-warn'}`;
            li.innerHTML = `<i class="ti ${item.ok ? 'ti-circle-check' : 'ti-alert-circle'}" aria-hidden="true"></i>`;
            const text = document.createElement('span');
            text.textContent = item.ok ? item.okText : item.ngText;
            li.appendChild(text);
            if (!item.ok && item.action) {
                const fix = document.createElement('button');
                fix.type = 'button';
                fix.className = 'ml-auto whitespace-nowrap';
                fix.textContent = '設定する';
                fix.addEventListener('click', () => { publishDialog.close(); item.action(); });
                li.appendChild(fix);
            }
            list.appendChild(li);
            blocked = blocked || (!item.ok && item.blocking);
        });
        $('[data-confirm-publish]', publishDialog).disabled = blocked;
    }

    function updatePublishLabel() {
        const schedule = $('input[name=publish_timing][value=schedule]', publishDialog).checked;
        const when = $('[data-publish-at]', publishDialog).value;
        const future = schedule && when && new Date(when) > new Date();
        $('[data-confirm-publish-label]', publishDialog).textContent = future ? '予約する' : '公開する';
    }

    if (publishButton && publishDialog && typeof publishDialog.showModal === 'function') {
        const publishAt = $('[data-publish-at]', publishDialog);
        publishButton.addEventListener('click', (event) => {
            event.preventDefault();
            $('[data-publish-title]', publishDialog).textContent = titleInput.value || 'タイトル未設定';
            const preset = publishedAtField.value;
            $(`input[name=publish_timing][value=${preset ? 'schedule' : 'now'}]`, publishDialog).checked = true;
            publishAt.value = preset || toLocalInputValue(new Date(Date.now() + 60 * 60 * 1000));
            buildChecklist();
            updatePublishLabel();
            publishDialog.showModal();
        });
        $$('input[name=publish_timing]', publishDialog).forEach((radio) => radio.addEventListener('change', updatePublishLabel));
        publishAt.addEventListener('input', () => {
            $('input[name=publish_timing][value=schedule]', publishDialog).checked = true;
            updatePublishLabel();
        });
        $('[data-confirm-publish]', publishDialog).addEventListener('click', () => {
            const schedule = $('input[name=publish_timing][value=schedule]', publishDialog).checked;
            publishedAtField.value = schedule ? publishAt.value : '';
            publishDialog.close();
            form.requestSubmit(publishButton);
        });
    }

    // ------------------------------------------------------------------
    // Local autosave & restore
    // ------------------------------------------------------------------
    const autosaveFields = ['title', 'content', 'excerpt', 'tags'];
    const storage = (() => {
        try {
            const probe = '__techblog_probe__';
            localStorage.setItem(probe, probe);
            localStorage.removeItem(probe);
            return localStorage;
        } catch (error) {
            return null;
        }
    })();

    function currentSnapshot() {
        const snapshot = {};
        autosaveFields.forEach((name) => {
            const field = form.elements[name];
            snapshot[name] = field ? field.value : '';
        });
        return snapshot;
    }

    function sameAsForm(snapshot) {
        const current = currentSnapshot();
        return autosaveFields.every((name) => (snapshot[name] || '') === (current[name] || ''));
    }

    const writeLocalDraft = debounce(() => {
        if (!storage) {
            setStatus('未保存の変更があります', { dirty: true });
            return;
        }
        const payload = { ...currentSnapshot(), savedAt: Date.now(), baseUpdatedAt: config.serverUpdatedAt };
        try {
            storage.setItem(config.storageKey, JSON.stringify(payload));
            setStatus(`未保存（ブラウザに一時保存 ${timeFormat.format(new Date())}）`, { dirty: true });
        } catch (error) {
            setStatus('未保存の変更があります', { dirty: true });
        }
    }, 800);

    let restoreSnapshot = null;
    if (storage) {
        // A successful save of the form we submitted: its local backup is no longer needed.
        try {
            const submittedKey = sessionStorage.getItem('techblog:editor:submitted');
            sessionStorage.removeItem('techblog:editor:submitted');
            if (config.justSaved && submittedKey) {
                storage.removeItem(submittedKey);
            }
        } catch (error) { /* storage unavailable */ }

        try {
            restoreSnapshot = JSON.parse(storage.getItem(config.storageKey) || 'null');
        } catch (error) {
            restoreSnapshot = null;
        }
        if (restoreSnapshot && sameAsForm(restoreSnapshot)) {
            storage.removeItem(config.storageKey);
            restoreSnapshot = null;
        }
    }

    // ------------------------------------------------------------------
    // Tag chips with suggestions (the real field stays a comma-separated input)
    // ------------------------------------------------------------------
    const tagEditor = $('[data-tag-editor]');
    if (tagEditor && tagsField) {
        const maxTags = parseInt(tagEditor.dataset.maxTags, 10) || 5;
        const knownTags = JSON.parse(($('#editor-tag-names') || {}).textContent || '[]');
        const splitTags = (value) => {
            const seen = new Set();
            return (value || '').split(/[,、，]/).map((name) => name.trim().replace(/^#/, '')).filter((name) => {
                const key = name.toLowerCase();
                if (!name || seen.has(key)) {
                    return false;
                }
                seen.add(key);
                return true;
            });
        };

        tagsField.type = 'hidden';
        const field = document.createElement('div');
        field.className = 'ed-tags-field';
        tagEntry = document.createElement('input');
        tagEntry.type = 'text';
        tagEntry.className = 'ed-tag-input';
        tagEntry.setAttribute('aria-label', `タグ（最大${maxTags}個）`);
        tagEntry.setAttribute('role', 'combobox');
        tagEntry.setAttribute('aria-autocomplete', 'list');
        tagEntry.setAttribute('aria-expanded', 'false');
        tagEntry.setAttribute('aria-controls', 'tag-suggestions');
        tagEntry.autocomplete = 'off';
        field.appendChild(tagEntry);
        const suggest = document.createElement('ul');
        suggest.id = 'tag-suggestions';
        suggest.className = 'ed-suggest hidden';
        suggest.setAttribute('role', 'listbox');
        const hint = document.createElement('p');
        hint.className = 'ed-hint';
        tagEditor.append(field, suggest, hint);

        let activeIndex = -1;
        const tags = () => splitTags(tagsField.value);

        function closeSuggest() {
            suggest.classList.add('hidden');
            tagEntry.setAttribute('aria-expanded', 'false');
            tagEntry.removeAttribute('aria-activedescendant');
            activeIndex = -1;
        }

        function setTags(list) {
            tagsField.value = list.join(', ');
            tagsField.dispatchEvent(new Event('input', { bubbles: true }));
            renderTags();
        }

        function addTag(name) {
            const clean = name.trim().replace(/^#/, '').slice(0, 50);
            const list = tags();
            if (!clean) {
                return;
            }
            if (list.length >= maxTags) {
                hint.textContent = `タグは${maxTags}個までです。`;
                return;
            }
            const existing = knownTags.find((tag) => tag.toLowerCase() === clean.toLowerCase());
            if (!list.some((tag) => tag.toLowerCase() === clean.toLowerCase())) {
                list.push(existing || clean);
            }
            setTags(list);
            tagEntry.value = '';
            closeSuggest();
        }

        renderTags = () => {
            const list = tags();
            field.querySelectorAll('.ed-tag-chip').forEach((chip) => chip.remove());
            list.forEach((name) => {
                const chip = document.createElement('span');
                chip.className = 'ed-tag-chip';
                chip.textContent = `#${name}`;
                const remove = document.createElement('button');
                remove.type = 'button';
                remove.setAttribute('aria-label', `タグ「${name}」を外す`);
                remove.innerHTML = '<i class="ti ti-x" aria-hidden="true"></i>';
                remove.addEventListener('click', () => {
                    setTags(tags().filter((tag) => tag !== name));
                    tagEntry.focus();
                });
                chip.appendChild(remove);
                field.insertBefore(chip, tagEntry);
            });
            tagEntry.placeholder = list.length
                ? (list.length < maxTags ? 'タグを追加' : '')
                : `タグを追加（最大${maxTags}個・Enter で確定）`;
            hint.textContent = '';
        };

        function openSuggest() {
            const query = tagEntry.value.trim().replace(/^#/, '').toLowerCase();
            const current = tags().map((tag) => tag.toLowerCase());
            const matches = knownTags
                .filter((tag) => !current.includes(tag.toLowerCase()))
                .filter((tag) => !query || tag.toLowerCase().includes(query))
                .slice(0, 8);
            suggest.innerHTML = '';
            const addOption = (label, onPick) => {
                const option = document.createElement('li');
                option.id = `tag-option-${suggest.children.length}`;
                option.setAttribute('role', 'option');
                option.setAttribute('aria-selected', 'false');
                option.textContent = label;
                option.addEventListener('mousedown', (event) => {
                    event.preventDefault();
                    onPick();
                });
                suggest.appendChild(option);
            };
            matches.forEach((tag) => addOption(`#${tag}`, () => addTag(tag)));
            if (query && !knownTags.some((tag) => tag.toLowerCase() === query)) {
                addOption(`「${tagEntry.value.trim()}」を新しいタグとして追加`, () => addTag(tagEntry.value));
            }
            const visible = suggest.children.length > 0 && tags().length < maxTags;
            suggest.classList.toggle('hidden', !visible);
            tagEntry.setAttribute('aria-expanded', String(visible));
            activeIndex = -1;
        }

        function moveActive(delta) {
            const options = $$('[role=option]', suggest);
            if (!options.length) {
                return;
            }
            activeIndex = (activeIndex + delta + options.length) % options.length;
            options.forEach((option, index) => option.setAttribute('aria-selected', String(index === activeIndex)));
            tagEntry.setAttribute('aria-activedescendant', options[activeIndex].id);
            options[activeIndex].scrollIntoView({ block: 'nearest' });
        }

        tagEntry.addEventListener('focus', openSuggest);
        tagEntry.addEventListener('blur', () => setTimeout(closeSuggest, 100));
        tagEntry.addEventListener('input', () => {
            if (/[,、，]/.test(tagEntry.value)) {
                const parts = tagEntry.value.split(/[,、，]/);
                parts.slice(0, -1).forEach(addTag);
                tagEntry.value = parts.pop();
            }
            openSuggest();
        });
        tagEntry.addEventListener('keydown', (event) => {
            if (event.isComposing) {
                return;
            }
            if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
                event.preventDefault();
                if (suggest.classList.contains('hidden')) {
                    openSuggest();
                }
                moveActive(event.key === 'ArrowDown' ? 1 : -1);
            } else if (event.key === 'Enter') {
                event.preventDefault();
                const options = $$('[role=option]', suggest);
                if (activeIndex >= 0 && options[activeIndex]) {
                    options[activeIndex].dispatchEvent(new MouseEvent('mousedown'));
                } else if (tagEntry.value.trim()) {
                    addTag(tagEntry.value);
                } else {
                    textarea.focus();
                }
            } else if (event.key === 'Backspace' && !tagEntry.value) {
                const list = tags();
                list.pop();
                setTags(list);
            } else if (event.key === 'Escape') {
                closeSuggest();
            }
        });
        // Commit a half-typed tag when the form is submitted.
        form.addEventListener('submit', () => {
            if (tagEntry.value.trim()) {
                addTag(tagEntry.value);
            }
        }, true);
        field.addEventListener('click', (event) => {
            if (event.target === field) {
                tagEntry.focus();
            }
        });
        renderTags();
    }

    // Restore banner (after the tag editor exists so restored tags render as chips)
    if (restoreSnapshot) {
        const banner = $('#restore-banner');
        const when = new Date(restoreSnapshot.savedAt);
        const newerOnServer = config.serverUpdatedAt && restoreSnapshot.baseUpdatedAt && restoreSnapshot.baseUpdatedAt !== config.serverUpdatedAt;
        $('[data-restore-message]', banner).textContent =
            `保存されていない編集内容がブラウザに残っています（${when.toLocaleString('ja-JP')}）。` +
            (newerOnServer ? ' その後にサーバー上の記事が更新されています。' : '');
        banner.classList.remove('hidden');
        $('[data-restore-accept]', banner).addEventListener('click', () => {
            autosaveFields.forEach((name) => {
                if (form.elements[name] && typeof restoreSnapshot[name] === 'string') {
                    form.elements[name].value = restoreSnapshot[name];
                }
            });
            banner.classList.add('hidden');
            dirty = true;
            renderTags();
            refreshAll();
            setStatus('復元しました（まだ保存されていません）', { dirty: true });
        });
        $('[data-restore-discard]', banner).addEventListener('click', () => {
            storage.removeItem(config.storageKey);
            banner.classList.add('hidden');
        });
    }

    autosaveFields.forEach((name) => {
        const field = form.elements[name];
        if (field) {
            field.addEventListener('input', writeLocalDraft);
        }
    });

    // ------------------------------------------------------------------
    // Preview (rendered by the same server pipeline as the public page)
    // ------------------------------------------------------------------
    let previewRequest = 0;
    async function updatePreview() {
        if (body.dataset.mode === 'write') {
            return;
        }
        $('[data-preview-title]').textContent = titleInput.value.trim() || 'タイトル未設定';
        const tagBox = $('[data-preview-tags]');
        tagBox.innerHTML = '';
        (tagsField.value || '').split(',').map((name) => name.trim()).filter(Boolean).forEach((name) => {
            const chip = document.createElement('span');
            chip.className = 'chip';
            chip.textContent = `#${name}`;
            tagBox.appendChild(chip);
        });

        const text = textarea.value;
        if (!text.trim()) {
            preview.innerHTML = '<p class="text-gray-400">本文を書くとここにプレビューが表示されます。</p>';
            return;
        }
        const requestId = ++previewRequest;
        const payload = new URLSearchParams({ text });
        if (config.articleSlug) {
            payload.set('article', config.articleSlug);
        }
        try {
            const response = await fetch(config.previewUrl, {
                method: 'POST',
                headers: { [config.csrfHeader]: csrfToken() },
                body: payload,
                credentials: 'same-origin',
            });
            if (!response.ok || !(response.headers.get('content-type') || '').includes('json')) {
                throw new Error(`HTTP ${response.status}`);
            }
            const data = await response.json();
            if (requestId === previewRequest) {
                preview.innerHTML = data.html || '';
            }
        } catch (error) {
            if (requestId === previewRequest) {
                preview.innerHTML = '<div class="alert alert-warning">プレビューを取得できませんでした。ログインの有効期限が切れた可能性があります。'
                    + '入力内容はブラウザに一時保存されているので、別のタブでログインし直してから保存してください。</div>';
            }
        }
    }
    const updatePreviewDebounced = debounce(updatePreview, 300);

    // ------------------------------------------------------------------
    // Stats & counters
    // ------------------------------------------------------------------
    const stats = $('#content-stats');
    function updateStats() {
        const chars = textarea.value.replace(/\s/g, '').length;
        const minutes = Math.max(1, Math.round(chars / 500));
        if (stats) {
            stats.textContent = `${chars.toLocaleString('ja-JP')} 文字 ・ 約${minutes}分で読めます`;
        }
    }

    function updateCounters() {
        $$('[data-count-for]').forEach((counter) => {
            const field = document.getElementById(counter.dataset.countFor);
            if (field) {
                counter.textContent = field.value.length;
            }
        });
    }
    $$('[data-count-for]').forEach((counter) => {
        const field = document.getElementById(counter.dataset.countFor);
        if (field) {
            field.addEventListener('input', updateCounters);
        }
    });

    // ------------------------------------------------------------------
    // Cover image
    // ------------------------------------------------------------------
    const coverInput = $('#cover_image');
    const cover = $('[data-cover]');
    const addCover = $('[data-add-cover]');
    const removeCoverInput = $('[data-remove-cover-input]');
    const previewCover = $('[data-preview-cover]');
    function showCover(src) {
        $('[data-cover-img]').src = src;
        previewCover.src = src;
        cover.classList.toggle('hidden', !src);
        previewCover.classList.toggle('hidden', !src);
        addCover.hidden = Boolean(src);
    }
    coverInput.addEventListener('change', () => {
        const file = coverInput.files && coverInput.files[0];
        if (file) {
            removeCoverInput.value = '';
            showCover(URL.createObjectURL(file));
            dirty = true;
        }
    });
    $('[data-remove-cover]').addEventListener('click', () => {
        coverInput.value = '';
        removeCoverInput.value = '1';
        showCover('');
        dirty = true;
    });

    // ------------------------------------------------------------------
    // View mode (write / split / preview) and scroll sync
    // ------------------------------------------------------------------
    const modeButtons = $$('[data-view-mode]');
    function setMode(mode) {
        if (mode === 'split' && !window.matchMedia('(min-width: 1024px)').matches) {
            mode = 'write';
        }
        body.dataset.mode = mode;
        modeButtons.forEach((button) => button.setAttribute('aria-pressed', String(button.dataset.viewMode === mode)));
        try {
            localStorage.setItem('techblog:editor:mode', mode);
        } catch (error) { /* storage unavailable */ }
        grow(titleInput);
        grow(textarea);
        if (mode !== 'write') {
            updatePreview();
        }
        if (mode === 'preview') {
            window.scrollTo(0, 0);
        }
    }
    modeButtons.forEach((button) => button.addEventListener('click', () => setMode(button.dataset.viewMode)));
    $$('[data-toggle-preview]').forEach((button) => button.addEventListener('click', () => {
        setMode(body.dataset.mode === 'preview' ? 'write' : 'preview');
    }));

    const previewScroller = $('.ed-preview');
    writeScroller.addEventListener('scroll', () => {
        if (body.dataset.mode !== 'split') {
            return;
        }
        const ratio = writeScroller.scrollTop / ((writeScroller.scrollHeight - writeScroller.clientHeight) || 1);
        previewScroller.scrollTop = ratio * (previewScroller.scrollHeight - previewScroller.clientHeight);
    });

    // ------------------------------------------------------------------
    // Images: upload immediately and insert Markdown at the cursor
    // ------------------------------------------------------------------
    const imagePicker = $('#image-picker');
    const imageList = $('#image-list');
    const imageErrors = $('#image-errors');
    const itemTemplate = $('#image-item-template');

    function showImageError(message) {
        const line = document.createElement('p');
        line.textContent = message;
        imageErrors.appendChild(line);
        toast(message, { error: true });
    }

    function updateImageCount() {
        const count = $$('.image-item', imageList).length;
        $$('[data-image-count]').forEach((el) => { el.textContent = count; });
        const empty = $('[data-empty-images]', imageList);
        if (empty && count) {
            empty.remove();
        }
    }

    function altFromFilename(name) {
        return (name || '画像').replace(/\.[^.]+$/, '').replace(/[-_]+/g, ' ').trim() || '画像';
    }

    function markdownFor(item) {
        return `![${altFromFilename(item.dataset.filename)}](${item.dataset.markdownPath})`;
    }

    function bindImageItem(item) {
        $('[data-insert-image]', item).addEventListener('click', () => {
            if (body.dataset.mode === 'preview') {
                setMode('write');
            }
            insertBlock(markdownFor(item));
            toast('画像を本文に挿入しました');
        });
        $('[data-delete-image]', item).addEventListener('click', async () => {
            const used = textarea.value.includes(item.dataset.markdownPath) || textarea.value.includes(`](${item.dataset.filename})`);
            const message = used
                ? 'この画像は本文で使われています。削除すると本文の画像が表示されなくなります。削除しますか？'
                : 'この画像を削除しますか？';
            if (!window.confirm(message)) {
                return;
            }
            try {
                const response = await fetch(config.deleteUrlTemplate.replace('/0/', `/${item.dataset.imageId}/`), {
                    method: 'POST',
                    headers: { [config.csrfHeader]: csrfToken() },
                    credentials: 'same-origin',
                });
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                item.remove();
                updateImageCount();
            } catch (error) {
                showImageError('画像を削除できませんでした。');
            }
        });
    }

    function addImageItem(data) {
        const item = itemTemplate.content.firstElementChild.cloneNode(true);
        item.dataset.imageId = data.id;
        item.dataset.markdownPath = data.markdown_path;
        item.dataset.filename = data.filename;
        $('img', item).src = data.url;
        const label = $('[data-filename-label]', item);
        label.textContent = data.filename;
        label.title = data.markdown_path;
        $('[data-delete-image]', item).setAttribute('aria-label', `${data.filename} を削除`);
        if (!config.articleSlug) {
            // New article: attach the upload to the article when the form is saved.
            const hidden = document.createElement('input');
            hidden.type = 'hidden';
            hidden.name = 'inline_image_ids';
            hidden.value = data.id;
            item.appendChild(hidden);
        }
        imageList.appendChild(item);
        bindImageItem(item);
        updateImageCount();
        return item;
    }

    async function uploadImage(file, { insert = true } = {}) {
        if (!file || !file.type.startsWith('image/')) {
            return;
        }
        const filename = file.name && file.name !== 'image.png' ? file.name : `pasted-${Date.now()}.png`;
        const placeholder = `![アップロード中: ${filename}]()`;
        if (insert) {
            if (body.dataset.mode === 'preview') {
                setMode('write');
            }
            insertBlock(placeholder);
        }
        const payload = new FormData();
        payload.append('image', file, filename);
        if (config.articleSlug) {
            payload.append('article', config.articleSlug);
        }
        setStatus(`画像をアップロードしています…（${filename}）`, { dirty: true });
        try {
            const response = await fetch(config.uploadUrl, {
                method: 'POST',
                headers: { [config.csrfHeader]: csrfToken() },
                body: payload,
                credentials: 'same-origin',
            });
            const data = await response.json().catch(() => ({}));
            if (!response.ok) {
                throw new Error(data.error || `アップロードに失敗しました (HTTP ${response.status})`);
            }
            const item = addImageItem(data);
            if (insert) {
                textarea.value = textarea.value.replace(placeholder, markdownFor(item));
                textarea.dispatchEvent(new Event('input', { bubbles: true }));
            }
            setStatus(`画像を追加しました（${data.filename}）`, { dirty: true });
        } catch (error) {
            if (insert) {
                textarea.value = textarea.value.replace(placeholder + '\n', '').replace(placeholder, '');
                textarea.dispatchEvent(new Event('input', { bubbles: true }));
            }
            showImageError(`${filename}: ${error.message}`);
        }
    }

    async function uploadFiles(files, options) {
        imageErrors.textContent = '';
        for (const file of Array.from(files)) {
            // Sequential keeps the inserted images in the order they were chosen.
            await uploadImage(file, options);
        }
    }

    $$('.image-item', imageList).forEach(bindImageItem);

    if (imagePicker) {
        // With JS, uploads happen immediately; drop the field name so the files are not sent twice.
        imagePicker.removeAttribute('name');
        imagePicker.addEventListener('change', async () => {
            await uploadFiles(imagePicker.files, { insert: true });
            imagePicker.value = '';
        });
    }

    function hasFiles(event) {
        return event.dataTransfer && Array.from(event.dataTransfer.types || []).includes('Files');
    }

    [[$('[data-drop-target]'), 'ed-dropping'], [$('[data-dropzone]'), 'is-dragover']].forEach(([target, activeClass]) => {
        if (!target) {
            return;
        }
        target.addEventListener('dragover', (event) => {
            if (hasFiles(event)) {
                event.preventDefault();
                target.classList.add(activeClass);
            }
        });
        target.addEventListener('dragleave', (event) => {
            if (!target.contains(event.relatedTarget)) {
                target.classList.remove(activeClass);
            }
        });
        target.addEventListener('drop', (event) => {
            target.classList.remove(activeClass);
            if (!hasFiles(event)) {
                return;
            }
            event.preventDefault();
            textarea.focus();
            uploadFiles(event.dataTransfer.files, { insert: true });
        });
    });

    textarea.addEventListener('paste', (event) => {
        const files = Array.from((event.clipboardData && event.clipboardData.files) || []).filter((file) => file.type.startsWith('image/'));
        if (files.length) {
            event.preventDefault();
            uploadFiles(files, { insert: true });
        }
    });

    // ------------------------------------------------------------------
    // Wire up
    // ------------------------------------------------------------------
    function refreshAll() {
        grow(titleInput);
        grow(textarea);
        updateStats();
        updateCounters();
        updatePreview();
    }

    textarea.addEventListener('input', () => {
        grow(textarea);
        updateStats();
        updatePreviewDebounced();
    });
    titleInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && !event.isComposing) {
            event.preventDefault();
            (tagEntry || textarea).focus();
        }
    });
    titleInput.addEventListener('input', () => {
        if (/[\r\n]/.test(titleInput.value)) {
            titleInput.value = titleInput.value.replace(/[\r\n]+/g, ' ');
        }
        grow(titleInput);
        document.title = `${titleInput.value || '新しい記事'} - 編集`;
        updatePreviewDebounced();
    });
    tagsField.addEventListener('input', updatePreviewDebounced);
    window.addEventListener('resize', debounce(() => { grow(titleInput); grow(textarea); }, 150));

    let initialMode = 'write';
    try {
        initialMode = localStorage.getItem('techblog:editor:mode') || 'write';
    } catch (error) { /* storage unavailable */ }
    setMode(initialMode);
    refreshAll();
})();
