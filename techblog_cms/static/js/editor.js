/*
 * Article editor: Markdown toolbar & shortcuts, live server-side preview, local autosave
 * with restore, unsaved-changes guard, and instant image upload (picker, drag & drop, paste).
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
    const saveStatus = $('#save-status');
    const timeFormat = new Intl.DateTimeFormat('ja-JP', { hour: '2-digit', minute: '2-digit' });

    function debounce(fn, delay) {
        let timer = null;
        return (...args) => {
            clearTimeout(timer);
            timer = setTimeout(() => fn(...args), delay);
        };
    }

    function setStatus(text) {
        if (saveStatus) {
            saveStatus.textContent = text;
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
        const start = textarea.selectionStart;
        const before = value.substring(0, start);
        const after = value.substring(textarea.selectionEnd);
        const lead = before === '' || before.endsWith('\n\n') ? '' : (before.endsWith('\n') ? '\n' : '\n\n');
        const trail = after === '' || after.startsWith('\n\n') ? '\n' : (after.startsWith('\n') ? '\n' : '\n\n');
        const text = lead + block + trail;
        const caret = cursorOffset === null ? text.length : lead.length + cursorOffset;
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
            const block = '```' + language.trim() + '\n' + (code || '') + '\n```';
            insertBlock(block, 4 + language.trim().length);
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

    // ------------------------------------------------------------------
    // Saving: Ctrl+S, confirmations, unsaved-changes guard
    // ------------------------------------------------------------------
    const defaultSubmit = $('[data-default-submit]', form);
    let dirty = false;
    let submitting = false;

    document.addEventListener('keydown', (event) => {
        if ((event.ctrlKey || event.metaKey) && !event.altKey && event.key.toLowerCase() === 's') {
            event.preventDefault();
            if (defaultSubmit) {
                form.requestSubmit(defaultSubmit);
            }
        }
    });

    textarea.addEventListener('keydown', (event) => {
        if (!(event.ctrlKey || event.metaKey) || event.altKey) {
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

    form.addEventListener('input', () => {
        dirty = true;
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
            return;
        }
        const payload = { ...currentSnapshot(), savedAt: Date.now(), baseUpdatedAt: config.serverUpdatedAt };
        try {
            storage.setItem(config.storageKey, JSON.stringify(payload));
            setStatus(`未保存の変更あり（ブラウザに一時保存 ${timeFormat.format(new Date())}）`);
        } catch (error) {
            setStatus('未保存の変更があります');
        }
    }, 800);

    if (storage) {
        // A successful save of the form we submitted: its local backup is no longer needed.
        try {
            const submittedKey = sessionStorage.getItem('techblog:editor:submitted');
            sessionStorage.removeItem('techblog:editor:submitted');
            if (config.justSaved && submittedKey) {
                storage.removeItem(submittedKey);
            }
        } catch (error) { /* storage unavailable */ }

        let stored = null;
        try {
            stored = JSON.parse(storage.getItem(config.storageKey) || 'null');
        } catch (error) {
            stored = null;
        }
        if (stored && sameAsForm(stored)) {
            storage.removeItem(config.storageKey);
        } else if (stored) {
            const banner = $('#restore-banner');
            const when = new Date(stored.savedAt);
            const newerOnServer = config.serverUpdatedAt && stored.baseUpdatedAt && stored.baseUpdatedAt !== config.serverUpdatedAt;
            $('[data-restore-message]', banner).textContent =
                `保存されていない編集内容がブラウザに残っています（${when.toLocaleString('ja-JP')}）。` +
                (newerOnServer ? ' ※ その後にサーバー上の記事が更新されています。' : '');
            banner.classList.remove('hidden');
            $('[data-restore-accept]', banner).addEventListener('click', () => {
                autosaveFields.forEach((name) => {
                    if (form.elements[name] && typeof stored[name] === 'string') {
                        form.elements[name].value = stored[name];
                    }
                });
                banner.classList.add('hidden');
                dirty = true;
                refreshAll();
                setStatus('復元しました（まだ保存されていません）');
            });
            $('[data-restore-discard]', banner).addEventListener('click', () => {
                storage.removeItem(config.storageKey);
                banner.classList.add('hidden');
            });
        }
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
        const text = textarea.value;
        if (!text.trim()) {
            preview.innerHTML = '<p class="text-gray-400">プレビューがここに表示されます。</p>';
            return;
        }
        const requestId = ++previewRequest;
        const body = new URLSearchParams({ text });
        if (config.articleSlug) {
            body.set('article', config.articleSlug);
        }
        try {
            const response = await fetch(config.previewUrl, {
                method: 'POST',
                headers: { [config.csrfHeader]: csrfToken() },
                body,
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
    // Stats, counters, settings summary
    // ------------------------------------------------------------------
    const stats = $('#content-stats');
    function updateStats() {
        const chars = textarea.value.replace(/\s/g, '').length;
        const minutes = Math.max(1, Math.round(chars / 500));
        if (stats) {
            stats.textContent = `本文 ${chars.toLocaleString('ja-JP')} 文字 ・ 読了目安 約${minutes}分`;
        }
    }

    $$('[data-count-for]').forEach((counter) => {
        const field = document.getElementById(counter.dataset.countFor);
        if (!field) {
            return;
        }
        const update = () => { counter.textContent = field.value.length; };
        field.addEventListener('input', update);
        update();
    });

    const settingsSummary = $('[data-settings-summary]');
    const categorySelect = $('#category');
    const newCategory = $('#new_category');
    const tagsInput = $('#tags');
    const publishedAt = $('#published_at');
    const slugInput = $('#slug');

    function updateSettingsSummary() {
        if (!settingsSummary) {
            return;
        }
        const category = (newCategory && newCategory.value.trim())
            || (categorySelect && categorySelect.selectedOptions[0] ? categorySelect.selectedOptions[0].textContent : '');
        const tags = tagsInput && tagsInput.value.trim() ? tagsInput.value.trim() : 'なし';
        settingsSummary.textContent = `カテゴリ: ${category} ・ タグ: ${tags}`;
    }

    function updatePublishLabel() {
        const label = $('[data-publish-label]');
        if (!label || !publishedAt) {
            return;
        }
        const when = publishedAt.value ? new Date(publishedAt.value) : null;
        label.textContent = when && when > new Date() ? '予約公開する' : '公開する';
    }

    [categorySelect, newCategory, tagsInput].forEach((field) => field && field.addEventListener('input', updateSettingsSummary));
    if (categorySelect) {
        categorySelect.addEventListener('change', updateSettingsSummary);
    }
    if (publishedAt) {
        publishedAt.addEventListener('input', updatePublishLabel);
    }
    if (slugInput) {
        slugInput.addEventListener('input', () => {
            const target = $('[data-slug-preview]');
            if (target) {
                target.textContent = slugInput.value || '…';
            }
        });
    }

    $$('[data-add-tag]').forEach((button) => {
        button.addEventListener('click', () => {
            const names = tagsInput.value.split(/[,、，]/).map((name) => name.trim()).filter(Boolean);
            if (!names.some((name) => name.toLowerCase() === button.dataset.addTag.toLowerCase())) {
                names.push(button.dataset.addTag);
            }
            tagsInput.value = names.join(', ');
            tagsInput.dispatchEvent(new Event('input', { bubbles: true }));
        });
    });

    const coverInput = $('#cover_image');
    const coverPreview = $('[data-cover-preview]');
    if (coverInput && coverPreview) {
        coverInput.addEventListener('change', () => {
            const file = coverInput.files && coverInput.files[0];
            if (file) {
                coverPreview.src = URL.createObjectURL(file);
                coverPreview.classList.remove('hidden');
            }
        });
    }

    // ------------------------------------------------------------------
    // View mode (write / split / preview) and scroll sync
    // ------------------------------------------------------------------
    const panes = $('#editor-panes');
    const modeButtons = $$('[data-view-mode]');
    function setMode(mode) {
        if (mode === 'split' && !window.matchMedia('(min-width: 1024px)').matches) {
            mode = 'write';
        }
        panes.dataset.mode = mode;
        modeButtons.forEach((button) => button.setAttribute('aria-pressed', String(button.dataset.viewMode === mode)));
        try {
            localStorage.setItem('techblog:editor:mode', mode);
        } catch (error) { /* storage unavailable */ }
        if (mode !== 'write') {
            updatePreview();
        }
    }
    modeButtons.forEach((button) => button.addEventListener('click', () => setMode(button.dataset.viewMode)));
    let initialMode = 'split';
    try {
        initialMode = localStorage.getItem('techblog:editor:mode') || 'split';
    } catch (error) { /* storage unavailable */ }
    setMode(initialMode);

    textarea.addEventListener('scroll', () => {
        if (panes.dataset.mode !== 'split') {
            return;
        }
        const ratio = textarea.scrollTop / ((textarea.scrollHeight - textarea.clientHeight) || 1);
        preview.scrollTop = ratio * (preview.scrollHeight - preview.clientHeight);
    });

    // ------------------------------------------------------------------
    // Images: upload immediately and insert Markdown at the cursor
    // ------------------------------------------------------------------
    const imagePicker = $('#image-picker');
    const imageList = $('#image-list');
    const imageErrors = $('#image-errors');
    const imageCount = $('[data-image-count]');
    const imagesPanel = $('#images-panel');
    const itemTemplate = $('#image-item-template');

    function showImageError(message) {
        const line = document.createElement('p');
        line.textContent = message;
        imageErrors.appendChild(line);
    }

    function updateImageCount() {
        if (imageCount) {
            imageCount.textContent = $$('.image-item', imageList).length;
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
            insertBlock(markdownFor(item));
        });
        $('[data-delete-image]', item).addEventListener('click', async () => {
            const path = item.dataset.markdownPath;
            const used = textarea.value.includes(path) || textarea.value.includes(`](${item.dataset.filename})`);
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
        $('[data-filename-label]', item).textContent = data.filename;
        $('[data-path-label]', item).textContent = data.markdown_path;
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
        if (imagesPanel) {
            imagesPanel.open = true;
        }
        const filename = file.name && file.name !== 'image.png' ? file.name : `pasted-${Date.now()}.png`;
        const placeholder = `![アップロード中: ${filename}]()`;
        if (insert) {
            insertBlock(placeholder);
        }
        const body = new FormData();
        body.append('image', file, filename);
        if (config.articleSlug) {
            body.append('article', config.articleSlug);
        }
        setStatus(`画像をアップロードしています…（${filename}）`);
        try {
            const response = await fetch(config.uploadUrl, {
                method: 'POST',
                headers: { [config.csrfHeader]: csrfToken() },
                body,
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
            setStatus(`画像を追加しました（${data.filename}）`);
        } catch (error) {
            if (insert) {
                textarea.value = textarea.value.replace(placeholder + '\n', '').replace(placeholder, '');
                textarea.dispatchEvent(new Event('input', { bubbles: true }));
            }
            showImageError(`${filename}: ${error.message}`);
            setStatus('');
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

    [textarea, $('[data-dropzone]')].forEach((target) => {
        if (!target) {
            return;
        }
        target.addEventListener('dragover', (event) => {
            if (hasFiles(event)) {
                event.preventDefault();
                target.classList.add('is-dragover');
            }
        });
        target.addEventListener('dragleave', () => target.classList.remove('is-dragover'));
        target.addEventListener('drop', (event) => {
            target.classList.remove('is-dragover');
            if (!hasFiles(event)) {
                return;
            }
            event.preventDefault();
            if (target === textarea) {
                textarea.focus();
            }
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
        updateStats();
        updateSettingsSummary();
        updatePublishLabel();
        $$('[data-count-for]').forEach((counter) => {
            const field = document.getElementById(counter.dataset.countFor);
            if (field) {
                counter.textContent = field.value.length;
            }
        });
        updatePreview();
    }

    textarea.addEventListener('input', () => {
        updateStats();
        updatePreviewDebounced();
    });
    if (titleInput) {
        // The title is a one-line field that wraps: grow with the text, never accept newlines.
        const growTitle = () => {
            titleInput.style.height = 'auto';
            titleInput.style.height = `${titleInput.scrollHeight}px`;
        };
        titleInput.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' && !event.isComposing) {
                event.preventDefault();
                textarea.focus();
            }
        });
        titleInput.addEventListener('input', () => {
            if (/[\r\n]/.test(titleInput.value)) {
                titleInput.value = titleInput.value.replace(/[\r\n]+/g, ' ');
            }
            growTitle();
            document.title = `${titleInput.value || '新規記事'} - 編集`;
        });
        window.addEventListener('resize', debounce(growTitle, 100));
        growTitle();
    }

    refreshAll();
})();
