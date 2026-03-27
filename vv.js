// ==UserScript==
// @name         NotebookLM → Obsidian Export (V18 - Masterpiece)
// @namespace    http://tampermonkey.net/
// @version      18.0
// @description  Ultimate clean export. Surgical auto-crop, variable safe-naming, absolute format fidelity.
// @match        https://notebooklm.google.com/*
// @grant        none
// ==/UserScript==

(function () {
    'use strict';

    const CONFIG = {
        buttonColor: '#7c3aed',
        defaultFileNamePrefix: 'NotebookLM_Export_'
    };

    // ── 1. HARDENED FILTERS ────────────────────────────────────────────────
    const SKIP_TAGS = new Set(['SCRIPT', 'STYLE', 'NOSCRIPT', 'HEAD', 'META', 'LINK', 'BUTTON', 'INPUT', 'TEXTAREA', 'SELECT', 'OPTION', 'NAV', 'HEADER', 'FOOTER', 'DIALOG', 'SVG', 'IMG', 'IFRAME']);
    const BLOCK_TAGS = new Set(['P', 'DIV', 'SECTION', 'ARTICLE', 'ASIDE', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'BLOCKQUOTE', 'PRE', 'UL', 'OL', 'LI', 'TABLE', 'TR', 'TD', 'TH', 'HR', 'BR']);

    function isUIChrome(el) {
        if (!el || !el.getAttribute) return false;
        if (window.getComputedStyle) {
            const style = window.getComputedStyle(el);
            if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return true;
        }
        const role = (el.getAttribute('role') || '').toLowerCase();
        const aria = (el.getAttribute('aria-label') || '').toLowerCase();
        const className = (typeof el.className === 'string' ? el.className.toLowerCase() : '');

        if (['button', 'toolbar', 'navigation', 'menu', 'menuitem', 'dialog', 'tooltip', 'progressbar', 'presentation', 'tab', 'tablist'].includes(role)) return true;
        if (aria.includes('emoji') || aria.includes('loading') || aria.includes('menu') || aria.includes('action')) return true;
        if (className.includes('button') || className.includes('tooltip') || className.includes('spinner') || className.includes('emoji') || className.includes('avatar')) return true;

        return false;
    }

    // ── 2. PRECISE DOM EXTRACTION ──────────────────────────────────────────
    function extractText(node) {
        if (node.nodeType === Node.TEXT_NODE) {
            const t = node.textContent.trim();
            const uiStrings = ['Loading', 'No emoji found', 'Sources', 'Chat', 'Studio', 'Notebook guide', 'Saved to notes', 'Copy to clipboard'];
            if (uiStrings.includes(t)) return "";
            if (/^\d+\s*sources?$/i.test(t) || /^(?:Today|Yesterday)\s*•/i.test(t) || /^\d{1,2}:\d{2}\s*[AP]M$/.test(t)) return "";
            return node.textContent;
        }
        
        if (node.nodeType !== Node.ELEMENT_NODE) return "";
        const tag = node.tagName.toUpperCase();
        if (SKIP_TAGS.has(tag) || isUIChrome(node)) return "";

        let text = "";
        const isBlock = BLOCK_TAGS.has(tag);
        if (isBlock) text += "\n\n";

        if (tag === 'H1') text += "# ";
        else if (tag === 'H2') text += "## ";
        else if (tag === 'H3') text += "### ";
        else if (tag === 'BLOCKQUOTE') text += "> ";
        else if (tag === 'LI') text += "- ";
        else if (tag === 'STRONG' || tag === 'B') text += "**";
        else if (tag === 'EM' || tag === 'I') text += "*";

        for (const child of node.childNodes) text += extractText(child);

        if (tag === 'STRONG' || tag === 'B') text += "**";
        else if (tag === 'EM' || tag === 'I') text += "*";
        if (isBlock) text += "\n\n";

        return text;
    }

    // ── 3. SMART POST-PROCESSING & SURGICAL CROP ───────────────────────────
    function postProcessMarkdown(text) {
        text = text.replace(/-{4,}/g, '---');

        // 🔥 SURGICAL CROP: Find the true start of YAML and discard EVERYTHING before it.
        // This eliminates Summaries and Prompts completely.
        const yamlRegex = /(---[\s\n]*(?:channel|title|categories|tags|speaker)\s*:[\s\S]*)/i;
        const match = text.match(yamlRegex);
        if (match) {
            text = match[1]; 
        } else {
            // Hard fallback if YAML is missing but prompt is there
            text = text.replace(/task:\s*".*?"/gi, '');
            text = text.replace(/role:\s*>\s*[\s\S]*?(?=\n\n|$)/gi, '');
            text = text.replace(/output:[\s\S]*?begin_with:\s*\|/gi, '');
        }

        // YAML Formatting
        ['channel:', 'title:', 'categories:', 'tags:', 'speaker:'].forEach(key => {
            const regex = new RegExp(`(?<!\\n)\\s*(${key})`, 'gi');
            text = text.replace(regex, '\n$1');
        });

        // Close YAML
        if (text.includes('---')) {
            text = text.replace(/(speaker:[^\n]*)\n*(?=[^\n-])/i, '$1\n---\n\n');
        }
        text = text.replace(/(---[\s\S]*?---)/, (m) => m.replace(/\n{2,}/g, '\n'));

        // Format Speakers
        text = text.replace(/(?:\n|^|\s)\s*(\*?\*?(?:Host|Guest(?:\s*\([^)]+\))?|Speaker(?:\s*\d+)?)\*?\*?)\s*:/gi, '\n\n**$1:**\n');
        text = text.replace(/\*\*\*\*/g, '**');

        // Remove AI Double Asterisk Bleed (e.g. "**Host:**\n** Text")
        text = text.replace(/(\*\*(?:Host|Guest[^*]*|Speaker[^*]*)\*\*:\s*\n+)(?:\*\*\s*|\*\s*)+/gi, '$1');

        // Final Polish
        text = text.replace(/ {2,}/g, ' '); 
        text = text.replace(/\n{3,}/g, '\n\n'); 
        text = text.replace(/\n>\s*/g, '\n\n> ');

        return text.trim();
    }

    // ── 4. SAFE FILE NAMING ────────────────────────────────────────────────
    function getFileNameFromContent(content) {
        const dateStr = new Date().toISOString().split('T')[0];
        const defaultName = `${CONFIG.defaultFileNamePrefix}${dateStr}.md`;
        
        const titleMatch = content.match(/^title:\s*"([^"]+)"/m) || content.match(/^title:\s*(.+)$/m);
        
        if (titleMatch && titleMatch[1]) {
            let cleanTitle = titleMatch[1].trim();
            
            // 🛡️ HARDEN: Reject template variables like {{_thai_title_}} or {{title}}
            if (/\{\{.*\}\}/.test(cleanTitle)) {
                return defaultName;
            }
            
            cleanTitle = cleanTitle.replace(/\s+/g, '_').replace(/[\\/:*?"<>|]/g, '');
            if (cleanTitle.length > 0) return `${cleanTitle}.md`;
        }
        return defaultName;
    }

    // ── 5. EXECUTION ───────────────────────────────────────────────────────
    function findMainContentArea() {
        const selection = window.getSelection();
        if (selection && selection.toString().trim().length > 50) {
            const container = document.createElement('div');
            for (let i = 0; i < selection.rangeCount; i++) container.appendChild(selection.getRangeAt(i).cloneContents());
            return container;
        }

        const possibleAreas = document.querySelectorAll('main, article, [role="main"], [role="document"], .geS5n');
        let bestArea = document.body;
        let maxScore = 0;

        possibleAreas.forEach(area => {
            const score = area.innerText.length + (area.querySelectorAll('p').length * 100);
            if (score > maxScore && !isUIChrome(area)) { maxScore = score; bestArea = area; }
        });
        return bestArea;
    }

    function runExport(btn) {
        btn.innerText = 'Analyzing...';
        btn.style.backgroundColor = '#9333ea';

        setTimeout(() => {
            try {
                const targetElement = findMainContentArea();
                let rawText = extractText(targetElement);
                let cleanMarkdown = postProcessMarkdown(rawText);

                if (!cleanMarkdown || cleanMarkdown.length < 50) throw new Error("Content too short");

                const fileName = getFileNameFromContent(cleanMarkdown);
                const blob = new Blob([cleanMarkdown], { type: 'text/markdown;charset=utf-8' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url; a.download = fileName; document.body.appendChild(a); a.click();
                setTimeout(() => { document.body.removeChild(a); URL.revokeObjectURL(url); }, 100);
                
                btn.innerText = '✅ Success!';
                btn.style.backgroundColor = '#10b981';
            } catch (err) {
                console.error(err);
                btn.innerText = '❌ Failed - Highlight Text First';
                btn.style.backgroundColor = '#ef4444';
            }
            setTimeout(() => { btn.innerText = 'Export to Obsidian'; btn.style.backgroundColor = CONFIG.buttonColor; }, 4000);
        }, 150);
    }

    // ── 6. UI INJECTION ────────────────────────────────────────────────────
    function createButton() {
        if (document.getElementById('nblm-v18')) return;
        const btn = document.createElement('button');
        btn.id = 'nblm-v18'; btn.innerText = 'Export to Obsidian';
        Object.assign(btn.style, {
            position: 'fixed', bottom: '30px', right: '30px', zIndex: '999999', padding: '14px 20px',
            backgroundColor: CONFIG.buttonColor, color: '#fff', border: 'none', borderRadius: '12px',
            fontSize: '15px', fontWeight: 'bold', cursor: 'pointer', boxShadow: '0 4px 14px rgba(0,0,0,0.4)',
            transition: 'all 0.2s ease', minWidth: '160px', fontFamily: 'sans-serif'
        });
        btn.onmouseover = () => btn.style.transform = 'translateY(-2px)';
        btn.onmouseout = () => btn.style.transform = 'translateY(0)';
        btn.onclick = () => runExport(btn);
        document.body.appendChild(btn);
    }

    const observer = new MutationObserver(() => { if (!document.getElementById('nblm-v18')) createButton(); });
    observer.observe(document.body, { childList: true, subtree: true });
    createButton();

})();

