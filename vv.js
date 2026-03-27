// ==UserScript==
// @name         NotebookLM → Obsidian Export (V14 - Ultimate)
// @namespace    http://tampermonkey.net/
// @version      14.0
// @description  Full Review implementation. Fixes UI Chrome bleed, perfectly constructs YAML, and formats speakers.
// @match        https://notebooklm.google.com/*
// @grant        none
// ==/UserScript==

(function () {
    'use strict';

    const CONFIG = {
        buttonColor: '#7c3aed',
        fileNamePrefix: 'NotebookLM_Obsidian_'
    };

    // ── 1. HARDENED FILTERS ────────────────────────────────────────────────
    const SKIP_TAGS = new Set([
        'SCRIPT', 'STYLE', 'NOSCRIPT', 'HEAD', 'META', 'LINK',
        'BUTTON', 'INPUT', 'TEXTAREA', 'SELECT', 'OPTION',
        'NAV', 'HEADER', 'FOOTER', 'DIALOG', 'SVG', 'IMG', 'IFRAME'
    ]);

    const BLOCK_TAGS = new Set([
        'P', 'DIV', 'SECTION', 'ARTICLE', 'ASIDE',
        'H1', 'H2', 'H3', 'H4', 'H5', 'H6',
        'BLOCKQUOTE', 'PRE', 'UL', 'OL', 'LI',
        'TABLE', 'TR', 'TD', 'TH', 'HR', 'BR'
    ]);

    function isUIChrome(el) {
        if (!el || !el.getAttribute) return false;
        
        // 1. Check computed style for hidden elements (avoids tooltips)
        if (window.getComputedStyle) {
            const style = window.getComputedStyle(el);
            if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return true;
        }

        const role = (el.getAttribute('role') || '').toLowerCase();
        const aria = (el.getAttribute('aria-label') || '').toLowerCase();
        const className = (typeof el.className === 'string' ? el.className.toLowerCase() : '');

        // 2. Strict blacklisting
        if (['button', 'toolbar', 'navigation', 'menu', 'menuitem', 'dialog', 'tooltip', 'progressbar', 'presentation'].includes(role)) return true;
        if (aria.includes('emoji') || aria.includes('loading') || aria.includes('menu') || aria.includes('action')) return true;
        if (className.includes('button') || className.includes('tooltip') || className.includes('spinner') || className.includes('emoji') || className.includes('avatar')) return true;

        return false;
    }

    // ── 2. PRECISE DOM EXTRACTION ──────────────────────────────────────────
    function extractText(node) {
        if (node.nodeType === Node.TEXT_NODE) {
            // Drop useless empty text nodes or floating UI texts
            const text = node.textContent;
            if (text.trim() === 'Loading' || text.trim() === 'No emoji found') return "";
            return text;
        }
        
        if (node.nodeType !== Node.ELEMENT_NODE) return "";

        const tag = node.tagName.toUpperCase();
        if (SKIP_TAGS.has(tag)) return "";
        if (isUIChrome(node)) return "";

        let text = "";
        const isBlock = BLOCK_TAGS.has(tag);

        if (isBlock) text += "\n\n";

        // Map HTML tags to Markdown
        if (tag === 'H1') text += "# ";
        else if (tag === 'H2') text += "## ";
        else if (tag === 'H3') text += "### ";
        else if (tag === 'BLOCKQUOTE') text += "> ";
        else if (tag === 'LI') text += "- ";
        else if (tag === 'STRONG' || tag === 'B') text += "**";
        else if (tag === 'EM' || tag === 'I') text += "*";

        for (const child of node.childNodes) {
            text += extractText(child);
        }

        // Close inline formatting
        if (tag === 'STRONG' || tag === 'B') text += "**";
        else if (tag === 'EM' || tag === 'I') text += "*";

        if (isBlock) text += "\n\n";

        return text;
    }

    // ── 3. SMART POST-PROCESSING (Targeting 'Untitled 8' Exactness) ────────
    function postProcessMarkdown(text) {
        // Fix weird dashboard dashes
        text = text.replace(/-{4,}/g, '---');

        // Extract and format YAML Frontmatter keys
        const yamlKeys = ['channel:', 'title:', 'categories:', 'tags:', 'speaker:'];
        yamlKeys.forEach(key => {
            const regex = new RegExp(`(?<!\\n)\\s*(${key})`, 'gi');
            text = text.replace(regex, '\n$1');
        });

        // Ensure YAML closes properly
        if (text.includes('---')) {
            text = text.replace(/(speaker:[^\n]*)\n*(?=[^\n-])/i, '$1\n---\n\n');
        }

        // Format Speakers (e.g. "Host:", "Guest (Isaac):")
        // Makes them bold and moves dialogue to next line
        text = text.replace(/(?:\n|^|\s)\s*(\*?\*?(?:Host|Guest(?:\s*\([^)]+\))?|Speaker(?:\s*\d+)?)\*?\*?)\s*:/gi, '\n\n**$1:**\n');
        
        // Clean double bolding
        text = text.replace(/\*\*\*\*/g, '**');

        // Clean extra newlines and spaces
        text = text.replace(/ {2,}/g, ' '); 
        text = text.replace(/\n{3,}/g, '\n\n'); 
        
        // Fix Blockquote spacing
        text = text.replace(/\n>\s*/g, '\n\n> ');

        return text.trim();
    }

    // ── 4. EXECUTION & AUTO-TARGETING ──────────────────────────────────────
    function findMainContentArea() {
        const selection = window.getSelection();
        if (selection && selection.toString().trim().length > 50) {
            const container = document.createElement('div');
            for (let i = 0; i < selection.rangeCount; i++) {
                container.appendChild(selection.getRangeAt(i).cloneContents());
            }
            return container;
        }

        // Find the div with the most paragraph tags (highest text density)
        const possibleAreas = document.querySelectorAll('main, article, [role="main"], [role="document"], .geS5n');
        let bestArea = document.body;
        let maxScore = 0;

        possibleAreas.forEach(area => {
            const textLength = area.innerText.length;
            const pCount = area.querySelectorAll('p').length;
            const score = textLength + (pCount * 100);
            if (score > maxScore && !isUIChrome(area)) {
                maxScore = score;
                bestArea = area;
            }
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

                // Validation Guard
                if (!cleanMarkdown || cleanMarkdown.length < 50) {
                    throw new Error("Content too short or UI detected.");
                }

                downloadFile(cleanMarkdown);
                
                btn.innerText = '✅ Exported!';
                btn.style.backgroundColor = '#10b981';
            } catch (err) {
                console.error("Export Error: ", err);
                btn.innerText = '❌ Failed - Try Highlighting Text';
                btn.style.backgroundColor = '#ef4444';
            }

            setTimeout(() => {
                btn.innerText = 'Export to Obsidian';
                btn.style.backgroundColor = CONFIG.buttonColor;
            }, 4000);
        }, 150);
    }

    function downloadFile(content) {
        const dateStr = new Date().toISOString().split('T')[0];
        const fileName = `${CONFIG.fileNamePrefix}${dateStr}.md`;
        const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        setTimeout(() => { document.body.removeChild(a); URL.revokeObjectURL(url); }, 100);
    }

    // ── 5. UI INJECTION ────────────────────────────────────────────────────
    function createButton() {
        if (document.getElementById('nblm-v14')) return;
        const btn = document.createElement('button');
        btn.id = 'nblm-v14';
        btn.innerText = 'Export to Obsidian';
        
        Object.assign(btn.style, {
            position: 'fixed', bottom: '30px', right: '30px', zIndex: '999999',
            padding: '14px 20px', backgroundColor: CONFIG.buttonColor, color: '#fff',
            border: 'none', borderRadius: '12px', fontSize: '15px', fontWeight: 'bold',
            cursor: 'pointer', boxShadow: '0 4px 14px rgba(0,0,0,0.4)',
            transition: 'all 0.2s ease', minWidth: '160px', fontFamily: 'sans-serif'
        });

        btn.onmouseover = () => btn.style.transform = 'translateY(-2px)';
        btn.onmouseout = () => btn.style.transform = 'translateY(0)';
        btn.onclick = () => runExport(btn);
        document.body.appendChild(btn);
    }

    const observer = new MutationObserver(() => { if (!document.getElementById('nblm-v14')) createButton(); });
    observer.observe(document.body, { childList: true, subtree: true });
    createButton();

})();

