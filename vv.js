// ==UserScript==
// @name         NotebookLM to Obsidian (V12 - Perfect Layout)
// @namespace    http://tampermonkey.net/
// @version      12.0
// @description  Eliminates line squashing using strict Turndown block rules and line break injections.
// @match        https://notebooklm.google.com/*
// @require      https://unpkg.com/turndown/dist/turndown.js
// @require      https://unpkg.com/turndown-plugin-gfm/dist/turndown-plugin-gfm.js
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    function sanitizeDOM(container) {
        let clone = container.cloneNode(true);

        // 1. Remove UI junk components
        let junkSelectors = [
            'button', 'textarea', 'input', 'nav', 'header', 'svg', 'img',
            '[role="button"]', '[role="toolbar"]', '[role="navigation"]', '[role="menu"]',
            '[aria-label*="emoji"]', '[aria-label*="Recently used"]',
            '.cdk-overlay-container', '[class*="tooltip"]', '[class*="icon"]',
            '.clip-board-button'
        ];
        junkSelectors.forEach(selector => {
            clone.querySelectorAll(selector).forEach(el => el.remove());
        });

        // 2. Remove the user's prompt configuration block
        clone.querySelectorAll('pre, code, div').forEach(el => {
            let text = el.textContent || '';
            if (text.includes('task:') && text.includes('role:')) {
                el.remove();
            }
        });

        return clone;
    }

    function postProcessMarkdown(md) {
        // 1. Unescape Markdown characters heavily guarded by Turndown
        md = md.replace(/\\=/g, '=');
        md = md.replace(/\\\*/g, '*');
        md = md.replace(/\\_/g, '_');
        md = md.replace(/\\\[/g, '[');
        md = md.replace(/\\\]/g, ']');
        md = md.replace(/\\-/g, '-');
        md = md.replace(/\\>/g, '>');

        // 2. Clean leftover string fragments from Google's UI
        let lines = md.split('\n');
        let cleanLines = lines.filter(line => {
            let t = line.trim();
            if (t === '') return true;
            let bad = [
                'Search results', 'No emoji found', 'Recently used', 
                'Loading', 'Start typing...', 'Save to note',
                'Chat', 'Studio', 'Sources', 'PLUS', '👁️',
                'SourcesChatStudio', 'SourcesChat', 'ChatStudio'
            ];
            if (bad.includes(t)) return false;
            if (/^[0-9]+\s+source(s)?$/.test(t)) return false;
            if (/^(Today|Yesterday|[A-Za-z]+)\s\u2022\s[0-9]{1,2}:[0-9]{2}\s(AM|PM)/i.test(t)) return false;
            return true;
        });
        md = cleanLines.join('\n');

        // 3. YAML FRONTMATTER RECONSTRUCTION
        // Strip out existing horizontal rules to prevent YAML breakage
        md = md.replace(/^-{4,}$/gm, '---'); 
        md = md.replace(/^\*{3,}$/gm, '---');

        // Ensure YAML keys start on fresh lines
        md = md.replace(/(\s*)(channel:\s*")/g, '\n$2');
        md = md.replace(/(\s*)(title:\s*")/g, '\n$2');
        md = md.replace(/(\s*)(categories:\s*\[)/g, '\n$2');
        md = md.replace(/(\s*)(tags:\s*\[)/g, '\n$2');
        md = md.replace(/(\s*)(speaker:\s*")/g, '\n$2');

        // Apply strict top and bottom boundaries for YAML
        if (md.includes('channel: "') && md.includes('speaker: "')) {
            md = md.replace(/^---\s*\n/gm, ''); // Remove floating dashes
            md = md.replace(/(channel:\s*")/g, '---\n$1');
            md = md.replace(/(speaker:\s*".*?")\s*/g, '$1\n---\n\n');
        }

        // 4. STRICT DIALOGUE FORMATTING (Hard Line Breaks)
        // Detects **Name:** and forces two spaces + newline to ensure 
        // standard Markdown engines render it on a separate line.
        md = md.replace(/\*\*([^\*\n]{1,40}):\*\*[ \t\xA0]*/g, '\n\n**$1:** \n');
        md = md.replace(/\*\*([^\*\n]{1,40})\*\*:[ \t\xA0]*/g, '\n\n**$1:** \n');

        // 5. HIGHLIGHT FIXES
        md = md.replace(/==\s+/g, '==');
        md = md.replace(/\s+==/g, '==');

        // 6. GLOBAL SPACING CLEANUP
        // Standardize all excess newlines into perfect paragraph breaks
        md = md.replace(/\n{3,}/g, '\n\n');
        
        // Remove duplicated YAML tops
        md = md.replace(/^---\n---\n/g, '---\n');

        return md.trim();
    }

    function triggerDownload(content) {
        let blob = new Blob([content], { type: 'text/markdown' });
        let url = window.URL.createObjectURL(blob);
        let a = document.createElement('a');
        
        let dateStr = new Date().toISOString().slice(0,10);
        let timeStr = new Date().toTimeString().slice(0,8).replace(/:/g, '');
        
        a.href = url;
        a.download = 'NotebookLM_Format_' + dateStr + '_' + timeStr + '.md';
        a.style.display = 'none';
        
        document.body.appendChild(a);
        a.click();
        
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }

    function exportToMarkdown() {
        let btn = document.getElementById('nblm-export-v12-btn');
        let originalText = btn.innerText;
        btn.innerText = 'Extracting...';
        btn.style.backgroundColor = '#9ca3af';
        btn.style.color = '#111827';

        try {
            if (typeof TurndownService === 'undefined') {
                throw new Error("Turndown library is not loaded.");
            }

            let bestContainer = document.querySelector('main') || document.body;
            let maxScore = -1;
            document.querySelectorAll('div, main, section').forEach(container => {
                if (container.tagName === 'BODY' || container.tagName === 'HTML') return;
                let pCount = container.querySelectorAll('p').length;
                let textLen = container.innerText ? container.innerText.trim().length : 0;
                let score = pCount * 100 + textLen;
                if (textLen > document.body.innerText.length * 0.9) score = score / 2;
                if (score > maxScore && pCount > 0) {
                    maxScore = score;
                    bestContainer = container;
                }
            });

            let cleanDOM = sanitizeDOM(bestContainer);

            let turndownService = new TurndownService({
                headingStyle: 'atx',
                codeBlockStyle: 'fenced',
                bulletListMarker: '-',
                strongDelimiter: '**',
                emDelimiter: '*'
            });

            // CUSTOM RULE: Force strict paragraph breaks for block elements
            turndownService.addRule('strict_block_spacing', {
                filter: ['div', 'p', 'article', 'section'],
                replacement: function (content) {
                    return '\n\n' + content + '\n\n';
                }
            });

            // CUSTOM RULE: Convert line breaks into true structural breaks
            turndownService.addRule('br_spacing', {
                filter: ['br'],
                replacement: function () {
                    return '\n\n';
                }
            });
            
            if (typeof turndownPluginGfm !== 'undefined') {
                turndownService.use(turndownPluginGfm.gfm);
            }

            turndownService.escape = function(string) {
                return string; // Prevent Turndown from destroying custom syntax
            };

            let rawMarkdown = turndownService.turndown(cleanDOM.innerHTML);
            let finalMarkdown = postProcessMarkdown(rawMarkdown);

            if (!finalMarkdown || finalMarkdown === "") {
                throw new Error("No readable content found.");
            }

            triggerDownload(finalMarkdown);

            btn.innerText = 'Perfected!';
            btn.style.backgroundColor = '#10b981'; 
            btn.style.color = '#ffffff';
            setTimeout(() => {
                btn.innerText = originalText;
                btn.style.backgroundColor = '#991b1b';
                btn.style.color = '#ffffff';
            }, 2000);

        } catch (error) {
            console.error("Export Error: ", error);
            alert("Export failed: " + error.message);
            btn.innerText = 'Error';
            btn.style.backgroundColor = '#ef4444';
            btn.style.color = '#ffffff';
            setTimeout(() => {
                btn.innerText = originalText;
                btn.style.backgroundColor = '#991b1b';
                btn.style.color = '#ffffff';
            }, 2000);
        }
    }

    function createUI() {
        if (document.getElementById('nblm-export-v12-btn')) return;

        let btn = document.createElement('button');
        btn.id = 'nblm-export-v12-btn';
        btn.innerText = 'Export MD (V12 Perfect Layout)';
        
        btn.style.position = 'fixed';
        btn.style.bottom = '80px'; 
        btn.style.right = '24px';
        btn.style.zIndex = '999999';
        btn.style.padding = '14px 24px';
        btn.style.backgroundColor = '#991b1b'; // Crimson Red
        btn.style.color = '#ffffff';
        btn.style.border = '1px solid #7f1d1d';
        btn.style.borderRadius = '8px';
        btn.style.fontSize = '14px';
        btn.style.fontWeight = 'bold';
        btn.style.cursor = 'pointer';
        btn.style.boxShadow = '0 10px 15px -3px rgba(0, 0, 0, 0.5), 0 4px 6px -2px rgba(0, 0, 0, 0.25)';
        btn.style.transition = 'all 0.2s ease-in-out';

        btn.onmouseover = function() {
            if (btn.innerText === 'Export MD (V12 Perfect Layout)') {
                btn.style.transform = 'translateY(-2px)';
                btn.style.boxShadow = '0 0 15px rgba(220, 38, 38, 0.4)'; 
                btn.style.backgroundColor = '#b91c1c';
            }
        };
        btn.onmouseout = function() {
            if (btn.innerText === 'Export MD (V12 Perfect Layout)') {
                btn.style.transform = 'translateY(0)';
                btn.style.boxShadow = '0 10px 15px -3px rgba(0, 0, 0, 0.5)';
                btn.style.backgroundColor = '#991b1b';
            }
        };

        btn.onclick = exportToMarkdown;
        document.body.appendChild(btn);
    }

    let observer = new MutationObserver(function() {
        if (!document.getElementById('nblm-export-v12-btn')) {
            createUI();
        }
    });

    observer.observe(document.body, { childList: true, subtree: true });
    setTimeout(createUI, 1000);

})();
