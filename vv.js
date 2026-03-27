// ==UserScript==
// @name         NotebookLM to Obsidian (V11 - Ultimate Precision)
// @namespace    http://tampermonkey.net/
// @version      11.0
// @description  Forces exact YAML and Dialogue structures according to the user's strict prompt.
// @match        https://notebooklm.google.com/*
// @require      https://unpkg.com/turndown/dist/turndown.js
// @require      https://unpkg.com/turndown-plugin-gfm/dist/turndown-plugin-gfm.js
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    function sanitizeDOM(container) {
        let clone = container.cloneNode(true);

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

        clone.querySelectorAll('pre, code, div').forEach(el => {
            let text = el.textContent || '';
            // Remove the user's prompt configuration block
            if (text.includes('task:') && text.includes('role:')) {
                el.remove();
            }
        });

        return clone;
    }

    function postProcessMarkdown(md) {
        // 1. Unescape Turndown characters
        md = md.replace(/\\=/g, '=');
        md = md.replace(/\\\*/g, '*');
        md = md.replace(/\\_/g, '_');
        md = md.replace(/\\\[/g, '[');
        md = md.replace(/\\\]/g, ']');
        md = md.replace(/\\-/g, '-');
        md = md.replace(/\\>/g, '>');

        // 2. Clean UI junk
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
        // Fix NotebookLM horizontal rules squashing the YAML
        md = md.replace(/-{4,}/g, '---'); 
        md = md.replace(/\*{3,}/g, '---');

        // Force exact newlines before YAML keys
        md = md.replace(/(\s*)(channel:\s*")/g, '\n$2');
        md = md.replace(/(\s*)(title:\s*")/g, '\n$2');
        md = md.replace(/(\s*)(categories:\s*\[)/g, '\n$2');
        md = md.replace(/(\s*)(tags:\s*\[)/g, '\n$2');
        md = md.replace(/(\s*)(speaker:\s*")/g, '\n$2');

        // Fix missing bottom boundary of YAML block if squashed with text
        if (md.includes('channel: "')) {
            // Guarantee top boundary
            md = md.replace(/(channel:\s*")/g, '---\n$1');
            // Guarantee bottom boundary and separate from content
            md = md.replace(/(speaker:\s*".*?")([^\n])/g, '$1\n---\n\n$2');
        }

        // 4. STRICT DIALOGUE FORMATTING
        // Target **Name:** and force it to be on its own line, followed by the content on the next line.
        // Uses [^\*]+ to match any character (including non-English) without using non-English Regex.
        md = md.replace(/\*\*([^\*]+):\*\*\s*/g, '\n\n**$1:**\n');

        // 5. HIGHLIGHT FIXES
        md = md.replace(/==\s+/g, '==');
        md = md.replace(/\s+==/g, '==');

        // 6. STRICT PARAGRAPH SPACING
        // Reduce 3+ newlines to exactly 2 newlines (standard Markdown paragraph break)
        md = md.replace(/\n{3,}/g, '\n\n');

        // Cleanup any leading --- that got duplicated
        md = md.replace(/^---+[\s\n]*---/m, '---');

        return md.trim();
    }

    function triggerDownload(content) {
        let blob = new Blob([content], { type: 'text/markdown' });
        let url = window.URL.createObjectURL(blob);
        let a = document.createElement('a');
        
        let dateStr = new Date().toISOString().slice(0,10);
        let timeStr = new Date().toTimeString().slice(0,8).replace(/:/g, '');
        
        a.href = url;
        a.download = 'Interview_Translate_' + dateStr + '_' + timeStr + '.md';
        a.style.display = 'none';
        
        document.body.appendChild(a);
        a.click();
        
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }

    function exportToMarkdown() {
        let btn = document.getElementById('nblm-export-v11-btn');
        let originalText = btn.innerText;
        btn.innerText = 'Extracting...';
        btn.style.backgroundColor = '#d4d4d8';
        btn.style.color = '#000000';

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
            
            if (typeof turndownPluginGfm !== 'undefined') {
                turndownService.use(turndownPluginGfm.gfm);
            }

            turndownService.escape = function(string) {
                return string;
            };

            let rawMarkdown = turndownService.turndown(cleanDOM.innerHTML);
            let finalMarkdown = postProcessMarkdown(rawMarkdown);

            if (!finalMarkdown || finalMarkdown === "") {
                throw new Error("No readable content found.");
            }

            triggerDownload(finalMarkdown);

            btn.innerText = 'Success!';
            btn.style.backgroundColor = '#fbbf24'; 
            setTimeout(() => {
                btn.innerText = originalText;
                btn.style.backgroundColor = '#09090b';
                btn.style.color = '#fafafa';
            }, 2000);

        } catch (error) {
            console.error("Export Error: ", error);
            alert("Export failed: " + error.message);
            btn.innerText = 'Error';
            btn.style.backgroundColor = '#ef4444';
            btn.style.color = '#fafafa';
            setTimeout(() => {
                btn.innerText = originalText;
                btn.style.backgroundColor = '#09090b';
                btn.style.color = '#fafafa';
            }, 2000);
        }
    }

    function createUI() {
        if (document.getElementById('nblm-export-v11-btn')) return;

        let btn = document.createElement('button');
        btn.id = 'nblm-export-v11-btn';
        btn.innerText = 'Export to Obsidian';
        
        btn.style.position = 'fixed';
        btn.style.bottom = '80px'; 
        btn.style.right = '24px';
        btn.style.zIndex = '999999';
        btn.style.padding = '14px 24px';
        btn.style.backgroundColor = '#09090b'; 
        btn.style.color = '#fafafa';
        btn.style.border = '1px solid #27272a';
        btn.style.borderRadius = '8px';
        btn.style.fontSize = '14px';
        btn.style.fontWeight = 'bold';
        btn.style.cursor = 'pointer';
        btn.style.boxShadow = '0 10px 15px -3px rgba(0, 0, 0, 0.5), 0 4px 6px -2px rgba(0, 0, 0, 0.25)';
        btn.style.transition = 'all 0.2s ease-in-out';

        btn.onmouseover = function() {
            if (btn.innerText === 'Export to Obsidian') {
                btn.style.transform = 'translateY(-2px)';
                btn.style.boxShadow = '0 0 15px rgba(251, 191, 36, 0.4)'; 
                btn.style.borderColor = '#fbbf24'; 
            }
        };
        btn.onmouseout = function() {
            if (btn.innerText === 'Export to Obsidian') {
                btn.style.transform = 'translateY(0)';
                btn.style.boxShadow = '0 10px 15px -3px rgba(0, 0, 0, 0.5)';
                btn.style.borderColor = '#27272a';
            }
        };

        btn.onclick = exportToMarkdown;
        document.body.appendChild(btn);
    }

    let observer = new MutationObserver(function() {
        if (!document.getElementById('nblm-export-v11-btn')) {
            createUI();
        }
    });

    observer.observe(document.body, { childList: true, subtree: true });
    setTimeout(createUI, 1000);

})();
